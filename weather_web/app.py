"""Current-readings table page for the weather station.

This is the original pre-graphs UI (a plain HTML table of the current
reading plus today's min/max/avg) restored on top of the current data
pipeline: weather_daq writes to TimescaleDB now, not a local sqlite file,
so this reads TimescaleDB directly via db_api.WeatherDB instead of the old
sqlite-backed module. No charts, no history tab, no JS.
"""

from flask import Flask, Response, jsonify, redirect, url_for
import csv
import io
import json
import os
import datetime

import db_api
import web_settings

STATUS_FILE = os.environ.get('WEATHER_STATUS_FILE', '/tmp/weather_current.json')

app = Flask(__name__)


def validate_date_str(date_str):
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_sensor_faults():
    """Read the DAQ status file and return {name: message} for any sensor
    not reporting 'ok'. Never raises - a missing/unreadable file just means
    no banner, not a broken page."""
    try:
        with open(STATUS_FILE) as f:
            status = json.load(f)
    except Exception:
        return {}
    sensors = status.get('sensors') or {}
    return {
        name: info.get('message', 'fault')
        for name, info in sensors.items()
        if info.get('status') not in ('ok', 'unknown')
    }


@app.route('/api/weather_data', defaults={'date_str': None}, methods=['GET'])
@app.route('/api/weather_data/<date_str>', methods=['GET'])
def api_weather_data(date_str):
    if date_str and not validate_date_str(date_str):
        return "Invalid date format. Should be YYYY-MM-DD", 400
    today = datetime.date.today().strftime("%Y-%m-%d")
    date_str = date_str or today

    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    rows = weather_db.get_records_by_date(date_str)
    weather_db.close()
    return jsonify([dict(zip(db_api.COLS, (r[0].isoformat(), *r[1:]))) for r in rows])


@app.route('/api/weather_summary/<date_str>', methods=['GET'])
def api_weather_summary(date_str=None):
    if date_str and not validate_date_str(date_str):
        return "Invalid date format. Should be YYYY-MM-DD", 400
    today = datetime.date.today().strftime("%Y-%m-%d")
    date_str = date_str or today

    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    ds = weather_db.get_daily_summary(date_str)
    weather_db.close()
    return jsonify(ds)


@app.route('/api/data_export/csv/<date_str>', methods=['GET'])
def get_weather_csv(date_str):
    if date_str and not validate_date_str(date_str):
        return "Invalid date format. Should be YYYY-MM-DD", 400

    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    rows = weather_db.get_records_by_date(date_str)
    weather_db.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(db_api.COLS)
    writer.writerows(rows)
    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=weather_{date_str}.csv"},
    )


# route for backward compatibility
@app.route("/api/weather_web")
def home():
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    today = datetime.date.today().strftime("%Y-%m-%d")

    last = weather_db.get_last_record()
    cur_weather = last[0] if last else None
    ds = weather_db.get_daily_summary(today)
    weather_db.close()

    if cur_weather is None:
        return "<html><body><h1>No data yet</h1></body></html>"

    last_reading, cur_temp, cur_rh, cur_cpu_temp, cur_wind_speed, cur_wind_dir, cur_rain_qty = cur_weather

    alert_html = ''
    faults = get_sensor_faults()
    if faults:
        rows = ''.join(f"<div><strong>{name}</strong>: {msg}</div>" for name, msg in faults.items())
        alert_html = f"""
        <div style='background:#ffe0e0;border:1px solid #c00;padding:10px;margin-bottom:10px;color:#900;'>
            <strong>Sensor fault(s)</strong>
            {rows}
        </div>"""

    return f"""
    <html>
    <head>
        <title>Weather Data</title>
    </head>
    <body>
        <h1>Current Weather Data - Pavoorchatram, Tenkasi Dt., TN, India.</h1>
        {alert_html}
        <table border='1' cellpadding='5' cellspacing='0'>
            <tr><td>Last Reading</td><td>{last_reading}</td><td>Min</td><td>Max</td><td>Avg</td></tr>
            <tr><td>Temperature</td><td>{cur_temp} oC</td><td>{ds['temp']['min']}</td><td>{ds['temp']['max']}</td><td>{ds['temp']['avg']}</td></tr>
            <tr><td>Humidity</td><td>{cur_rh}% RH</td><td>{ds['rh']['min']}</td><td>{ds['rh']['max']}</td><td>{ds['rh']['avg']}</td></tr>
            <tr><td>Wind Speed</td><td>{cur_wind_speed}</td><td>&nbsp;</td><td>{ds['wind_speed']['max']}</td><td>{ds['wind_speed']['avg']}</td></tr>
            <tr><td>Wind Dir</td><td>{cur_wind_dir}</td><td>&nbsp;</td><td>&nbsp;</td><td>{ds['wind_dir']['avg']}</td></tr>
            <tr><td>Rain Qty</td><td>{cur_rain_qty}</td><td>&nbsp;</td><td>Total:</td><td>{ds['rain']['total']}</td></tr>
            <tr><td>CPU Temp</td><td>{cur_cpu_temp} oC</td><td>{ds['cpu_temp']['min']}</td><td>{ds['cpu_temp']['max']}</td><td>{ds['cpu_temp']['avg']}</td></tr>
        </table>
    </body>
    </html>
    """


@app.route('/')
def index():
    return redirect(url_for('home'))


if __name__ == "__main__":
    # Debug mode enables Werkzeug's interactive debugger, which allows remote
    # code execution if reachable on the network - never bind it to 0.0.0.0.
    debug_mode = os.environ.get('FLASK_DEBUG') == '1'
    host = "127.0.0.1" if debug_mode else "0.0.0.0"
    app.run(host=host, port=8000, debug=debug_mode)
