from flask import Flask, Response, jsonify, redirect, request, url_for, render_template
import csv
import io
import json
import sys
import os
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from weather_daq import db_api
import web_settings

COLS = ['id', 'timestamp', 'temp', 'rh', 'cpu_temp', 'wind_speed', 'wind_dir', 'rain_qty']
LIGHTNING_COLS = ['id', 'timestamp', 'event_type', 'distance_km', 'energy']
DHT_STATUS_FILE       = '/tmp/dht_status.json'
LIGHTNING_STATUS_FILE = '/tmp/lightning_status.json'

# Auto-seed the dev database when running locally (no Pi DB)
_dev_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weather_dev.db')
if web_settings.DB_SETTINGS['DB_FILE_NAME'] == _dev_db and not os.path.exists(_dev_db):
    try:
        import seed_dev_db
        seed_dev_db.seed()
    except Exception as e:
        print(f"[seed] Could not auto-seed dev DB: {e}")


def validate_date_str(date_str):
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_dht_status():
    try:
        with open(DHT_STATUS_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def get_lightning_i2c_status():
    try:
        with open(LIGHTNING_STATUS_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def assess_sensor_health(last_row, dht_status, lightning_i2c_status=None):
    health = {
        'dht22':     {'status': 'unknown', 'message': 'No status data'},
        'arduino':   {'status': 'unknown', 'message': 'No data'},
        'cpu':       {'status': 'unknown', 'message': 'No data'},
        'lightning': {'status': 'unknown', 'message': 'No status data'},
    }
    if not last_row:
        return health

    _, ts, temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty = last_row

    # DHT22
    if dht_status and dht_status.get('is_faulty'):
        health['dht22'] = {'status': 'fault', 'message': dht_status.get('last_error', 'Fault reported')}
    elif temp is not None and rh is not None:
        if temp < -40 or temp > 80:
            health['dht22'] = {'status': 'error', 'message': f'Temp out of range: {temp}°C'}
        elif rh < 0 or rh > 100:
            health['dht22'] = {'status': 'error', 'message': f'Humidity out of range: {rh}%'}
        else:
            health['dht22'] = {'status': 'ok', 'message': f'{temp}°C / {rh}% RH'}
    else:
        health['dht22'] = {'status': 'fault', 'message': 'Null readings from sensor'}

    # Arduino (wind + rain)
    if wind_speed is not None and wind_dir is not None:
        if wind_speed < 0:
            health['arduino'] = {'status': 'error', 'message': f'Negative wind speed: {wind_speed}'}
        elif not (0 <= wind_dir <= 360):
            health['arduino'] = {'status': 'error', 'message': f'Wind direction out of range: {wind_dir}°'}
        else:
            health['arduino'] = {'status': 'ok', 'message': f'{wind_speed} kph / {wind_dir}°'}
    else:
        health['arduino'] = {'status': 'fault', 'message': 'No wind data from Arduino'}

    # CPU
    if cpu_temp is not None:
        if cpu_temp > 85:
            health['cpu'] = {'status': 'error', 'message': f'Over-temperature: {cpu_temp}°C'}
        elif cpu_temp < 0:
            health['cpu'] = {'status': 'error', 'message': f'Out of range: {cpu_temp}°C'}
        else:
            health['cpu'] = {'status': 'ok', 'message': f'{cpu_temp}°C'}
    else:
        health['cpu'] = {'status': 'fault', 'message': 'No CPU temperature data'}

    # Lightning / AS3935 I2C
    if lightning_i2c_status is None:
        health['lightning'] = {'status': 'unknown', 'message': 'DAQ status file not found'}
    elif not lightning_i2c_status.get('is_connected'):
        err = lightning_i2c_status.get('last_error') or 'I2C not responding'
        health['lightning'] = {'status': 'fault', 'message': err}
    else:
        health['lightning'] = {'status': 'ok', 'message': 'I2C connected'}

    return health


app = Flask(__name__)


@app.route('/')
def index():
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/weather_web')
def home():
    return redirect(url_for('dashboard'))


@app.route('/api/weather_data/last24h')
def api_last24h():
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    rows = weather_db.get_last24h_records()
    return jsonify([dict(zip(COLS, row)) for row in rows])


@app.route('/api/weather_data', defaults={'date_str': None}, methods=['GET'])
@app.route('/api/weather_data/<date_str>', methods=['GET'])
def api_weather_data(date_str):
    if date_str and not validate_date_str(date_str):
        return "Invalid date format. Use YYYY-MM-DD", 400
    date_str = date_str or datetime.date.today().strftime("%Y-%m-%d")
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    rows = weather_db.get_records_by_date(date_str)
    return jsonify([dict(zip(COLS, row)) for row in rows])


@app.route('/api/weather_summary/<date_str>', methods=['GET'])
def api_weather_summary(date_str):
    if not validate_date_str(date_str):
        return "Invalid date format. Use YYYY-MM-DD", 400
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    return jsonify(weather_db.get_daily_summary(date_str))


@app.route('/api/sensor_status')
def api_sensor_status():
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    last = weather_db.get_last_record()
    last_row = last[0] if last else None
    dht_status = get_dht_status()
    lightning_i2c = get_lightning_i2c_status()
    health = assess_sensor_health(last_row, dht_status, lightning_i2c)
    return jsonify({
        'sensors': health,
        'last_reading': last_row[1] if last_row else None,
        'checked_at': datetime.datetime.now().isoformat(timespec='seconds'),
    })


@app.route('/api/data_export/csv/range/<start_date>/<end_date>', methods=['GET'])
def get_weather_csv_range(start_date, end_date):
    if not validate_date_str(start_date) or not validate_date_str(end_date):
        return "Invalid date format. Use YYYY-MM-DD", 400
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    rows = weather_db.get_records_by_date_range(start_date, end_date)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(COLS)
    writer.writerows(rows)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=weather_{start_date}_to_{end_date}.csv"},
    )


@app.route('/api/data_export/csv/<date_str>', methods=['GET'])
def get_weather_csv(date_str):
    if not validate_date_str(date_str):
        return "Invalid date format. Use YYYY-MM-DD", 400
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    rows = weather_db.get_records_by_date(date_str)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(COLS)
    writer.writerows(rows)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=weather_{date_str}.csv"},
    )


def _compute_storm_trend(strikes: list) -> str:
    """
    Given a list of recent lightning-only rows (ordered oldest→newest),
    return a human-readable trend string based on distance changes.
    """
    distances = [r[3] for r in strikes if r[2] == 'lightning' and r[3] is not None]
    if not distances:
        return 'clear'
    if distances[-1] <= 5:
        return 'overhead'
    if len(distances) < 3:
        return 'unknown'
    recent   = sum(distances[-3:]) / 3
    earlier  = sum(distances[:3])  / 3
    if recent < earlier - 2:
        return 'approaching'
    if recent > earlier + 2:
        return 'retreating'
    return 'stationary'


@app.route('/api/lightning/recent')
def api_lightning_recent():
    n = min(int(request.args.get('n', 20)), 200)
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    rows = weather_db.get_lightning_recent(n)
    return jsonify([dict(zip(LIGHTNING_COLS, r)) for r in rows])


@app.route('/api/lightning/today')
def api_lightning_today():
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    rows = weather_db.get_lightning_today()
    strikes = [r for r in rows if r[2] == 'lightning']
    return jsonify({
        'strikes':       [dict(zip(LIGHTNING_COLS, r)) for r in strikes],
        'strike_count':  len(strikes),
        'noise_count':   sum(1 for r in rows if r[2] == 'noise'),
        'disturber_count': sum(1 for r in rows if r[2] == 'disturber'),
    })


@app.route('/api/lightning/status')
def api_lightning_status():
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    last_24h = weather_db.get_lightning_last_hours(24)
    last_1h  = weather_db.get_lightning_last_hours(1)

    strikes_24h = [r for r in last_24h if r[2] == 'lightning']
    strikes_1h  = [r for r in last_1h  if r[2] == 'lightning']

    last_strike = strikes_24h[-1] if strikes_24h else None
    trend = _compute_storm_trend(last_24h)

    return jsonify({
        'last_strike_time':  last_strike[1] if last_strike else None,
        'last_distance_km':  last_strike[3] if last_strike else None,
        'last_energy':       last_strike[4] if last_strike else None,
        'strike_count_1h':   len(strikes_1h),
        'strike_count_24h':  len(strikes_24h),
        'storm_trend':       trend,
        'checked_at':        datetime.datetime.now().isoformat(timespec='seconds'),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)