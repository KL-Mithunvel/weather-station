"""Current-readings table page for the weather station.

This is the original pre-graphs UI (a plain HTML table of the current
reading plus today's min/max/avg) on top of the current data pipeline:
weather_daq writes to TimescaleDB, and this reads it directly via
db_api.WeatherDB. No charts, no history tab, no JS.

This page is meant to be reachable by the public (behind a Cloudflare Tunnel
and nginx), so it is written defensively:
  * every response is cached for CACHE_TTL seconds, so visitor traffic never
    turns into database load, and a database outage still serves the last good
    page for a while;
  * history requests are limited to the last MAX_HISTORY_DAYS days;
  * internal error text (database or sensor) is never shown to visitors;
  * strict security headers on every response.
"""

import csv
import datetime
import io
import json
import os
import threading
import time
from html import escape

import psycopg2
from flask import Flask, Response, jsonify, redirect, request
from werkzeug.exceptions import HTTPException

import db_api
import web_settings

STATUS_FILE = os.environ.get('WEATHER_STATUS_FILE', '/tmp/weather_current.json')

# How long a built page/API answer is reused, and how long a stale one may be
# served if the database is unreachable.
CACHE_TTL = 30
STALE_TTL = 600
# Oldest day a visitor may ask for. Keeps every query small and bounded.
MAX_HISTORY_DAYS = 31

# Public wording for sensor faults. The raw message from the DAQ (which can
# contain device paths or driver text) is deliberately not shown.
SENSOR_LABELS = {
    'dht22': 'Temperature / humidity sensor',
    'arduino': 'Wind / rain sensors',
    'cpu': 'Station computer',
}

app = Flask(__name__)
# No request on this site has a body.
app.config['MAX_CONTENT_LENGTH'] = 1024

_cache = {}
_cache_lock = threading.Lock()


def cached(key, builder):
    """Return builder()'s value, reusing it for CACHE_TTL seconds.

    If builder raises a database error, fall back to the last good value when
    it is younger than STALE_TTL; otherwise re-raise.
    """
    now = time.monotonic()
    with _cache_lock:
        hit = _cache.get(key)
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    try:
        value = builder()
    except psycopg2.Error:
        if hit and now - hit[0] < STALE_TTL:
            return hit[1]
        raise
    with _cache_lock:
        if len(_cache) > 200:
            _cache.clear()
        _cache[key] = (now, value)
    return value


def with_db(fn):
    """Run fn(db) on a short-lived read-only connection and always close it."""
    db = None
    try:
        db = db_api.WeatherDB(web_settings.DB_SETTINGS)
        return fn(db)
    finally:
        if db is not None:
            db.close()


def parse_date(date_str):
    """Return a date within the allowed window, or None if invalid/out of range."""
    try:
        day = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None
    today = datetime.date.today()
    if day > today or (today - day).days > MAX_HISTORY_DAYS:
        return None
    return day


def bad_date():
    return (f"Invalid date. Use YYYY-MM-DD within the last {MAX_HISTORY_DAYS} days.", 400,
            {'Content-Type': 'text/plain; charset=utf-8'})


def get_sensor_faults():
    """Return a list of public labels for sensors not reporting 'ok'.

    Never raises - a missing/unreadable file just means no banner.
    """
    try:
        with open(STATUS_FILE) as f:
            status = json.load(f)
    except Exception:
        return []
    sensors = status.get('sensors') or {}
    return [
        SENSOR_LABELS.get(name, 'A sensor')
        for name, info in sensors.items()
        if isinstance(info, dict) and info.get('status') not in ('ok', 'unknown')
    ]


@app.after_request
def security_headers(resp):
    h = resp.headers
    h['Content-Security-Policy'] = ("default-src 'none'; style-src 'unsafe-inline'; "
                                   "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
    h['X-Content-Type-Options'] = 'nosniff'
    h['X-Frame-Options'] = 'DENY'
    h['Referrer-Policy'] = 'no-referrer'
    h['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=(), payment=()'
    h['Cross-Origin-Opener-Policy'] = 'same-origin'
    h['Cross-Origin-Resource-Policy'] = 'same-origin'
    if request.headers.get('X-Forwarded-Proto') == 'https':
        h['Strict-Transport-Security'] = 'max-age=31536000'
    if resp.status_code == 200:
        h['Cache-Control'] = f'public, max-age={CACHE_TTL}'
    else:
        h['Cache-Control'] = 'no-store'
    return resp


def _plain(message, status, extra=None):
    headers = {'Content-Type': 'text/plain; charset=utf-8'}
    if extra:
        headers.update(extra)
    return message, status, headers


@app.errorhandler(psycopg2.Error)
def database_unavailable(exc):
    app.logger.error('database error: %s', str(exc).strip())
    return _plain('Weather data is temporarily unavailable. Please try again shortly.', 503,
                  {'Retry-After': '60'})


@app.errorhandler(HTTPException)
def http_error(exc):
    return _plain(exc.name, exc.code)


@app.errorhandler(Exception)
def unhandled_error(exc):
    app.logger.exception('unhandled error')
    return _plain('Internal server error', 500)


@app.route('/api/weather_data', defaults={'date_str': None}, methods=['GET'])
@app.route('/api/weather_data/<date_str>', methods=['GET'])
def api_weather_data(date_str):
    if date_str is None:
        day = datetime.date.today()
    else:
        day = parse_date(date_str)
        if day is None:
            return bad_date()
    iso = day.isoformat()
    rows = cached(('data', iso), lambda: with_db(lambda db: db.get_records_by_date(iso)))
    return jsonify([dict(zip(db_api.COLS, (r[0].isoformat(), *r[1:]))) for r in rows])


@app.route('/api/weather_summary/<date_str>', methods=['GET'])
def api_weather_summary(date_str):
    day = parse_date(date_str)
    if day is None:
        return bad_date()
    iso = day.isoformat()
    return jsonify(cached(('summary', iso), lambda: with_db(lambda db: db.get_daily_summary(iso))))


@app.route('/api/data_export/csv/<date_str>', methods=['GET'])
def get_weather_csv(date_str):
    day = parse_date(date_str)
    if day is None:
        return bad_date()
    iso = day.isoformat()
    rows = cached(('data', iso), lambda: with_db(lambda db: db.get_records_by_date(iso)))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(db_api.COLS)
    writer.writerows(rows)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=weather_{iso}.csv"},
    )


def _load_home(today):
    def query(db):
        return db.get_last_record(), db.get_daily_summary(today)
    return with_db(query)


def _row(label, current, vmin, vmax, vavg):
    cells = ''.join(f"<td>{escape(str(c))}</td>" for c in (current, vmin, vmax, vavg))
    return f"<tr><td>{escape(label)}</td>{cells}</tr>"


def _build_home():
    today = datetime.date.today().strftime("%Y-%m-%d")
    last, ds = _load_home(today)
    if not last:
        return "<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Weather Data</title></head>" \
               "<body><h1>No data yet</h1></body></html>"

    (last_reading, cur_temp, cur_rh, cur_cpu_temp,
     cur_wind_speed, cur_wind_dir, cur_rain_qty) = last[0]

    alert_html = ''
    faults = get_sensor_faults()
    if faults:
        rows = ''.join(f"<div><strong>{escape(name)}</strong>: not reporting normally</div>" for name in faults)
        alert_html = ("<div style='background:#ffe0e0;border:1px solid #c00;padding:10px;"
                      f"margin-bottom:10px;color:#900;'><strong>Sensor fault(s)</strong>{rows}</div>")

    nbsp = '&nbsp;'
    table_rows = [
        f"<tr><td>Last Reading</td><td>{escape(str(last_reading))}</td><td>Min</td><td>Max</td><td>Avg</td></tr>",
        _row('Temperature', f"{cur_temp} oC", ds['temp']['min'], ds['temp']['max'], ds['temp']['avg']),
        _row('Humidity', f"{cur_rh}% RH", ds['rh']['min'], ds['rh']['max'], ds['rh']['avg']),
        _row('Wind Speed', cur_wind_speed, nbsp, ds['wind_speed']['max'], ds['wind_speed']['avg']),
        _row('Wind Dir', cur_wind_dir, nbsp, nbsp, ds['wind_dir']['avg']),
        _row('Rain Qty', cur_rain_qty, nbsp, 'Total:', ds['rain']['total']),
        _row('CPU Temp', f"{cur_cpu_temp} oC", ds['cpu_temp']['min'], ds['cpu_temp']['max'], ds['cpu_temp']['avg']),
    ]
    # _row escapes its cells; the literal &nbsp; placeholders must survive.
    body = '\n            '.join(table_rows).replace('&amp;nbsp;', '&nbsp;')

    return f"""<!doctype html>
<html lang='en'>
<head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>Weather Data</title>
</head>
<body>
    <h1>Current Weather Data - Pavoorchatram, Tenkasi Dt., TN, India.</h1>
    {alert_html}
    <table border='1' cellpadding='5' cellspacing='0'>
            {body}
    </table>
</body>
</html>
"""


# route for backward compatibility
@app.route("/api/weather_web")
def home():
    html = cached(('home',), _build_home)
    return Response(html, mimetype='text/html')


@app.route('/')
def index():
    return redirect('/api/weather_web')


if __name__ == "__main__":
    # Development only. Production runs under gunicorn bound to 127.0.0.1
    # behind nginx. Never bind this to 0.0.0.0: debug mode would allow remote
    # code execution.
    app.run(host="127.0.0.1", port=8000, debug=os.environ.get('FLASK_DEBUG') == '1')
