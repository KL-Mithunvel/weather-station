from flask import Flask, Response, jsonify, redirect, url_for, render_template
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
DHT_STATUS_FILE = '/tmp/dht_status.json'

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


def assess_sensor_health(last_row, dht_status):
    health = {
        'dht22':   {'status': 'unknown', 'message': 'No status data'},
        'arduino': {'status': 'unknown', 'message': 'No data'},
        'cpu':     {'status': 'unknown', 'message': 'No data'},
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
    health = assess_sensor_health(last_row, dht_status)
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)