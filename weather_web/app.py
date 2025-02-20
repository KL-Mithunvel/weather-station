from flask import Flask, Response, jsonify
import csv
import io
import sys
import os
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from weather_daq import db_api
import web_settings


app = Flask(__name__)

@app.route('/api/weather_data', defaults={'date_str': None}, methods=['GET'])
@app.route('/api/weather_data/<date_str>', methods=['GET'])
def api_weather_data(date_str):
    today = datetime.date.today().strftime("%Y-%m-%d")
    date_str = date_str or today

    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    rows = weather_db.get_records_by_date(date_str)
    return jsonify(rows)


@app.route('/api/weather_summary/<date_str>', methods=['GET'])
def api_weather_summary(date_str=None):
    today = datetime.date.today().strftime("%Y-%m-%d")
    date_str = date_str or today

    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    ds = weather_db.get_daily_summary(date_str)
    return jsonify(ds)

@app.route('/api/data_export/csv/<date_str>', methods=['GET'])
def get_weather_csv(date_str):
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    weather_db.connect()
    rows = weather_db.get_records_by_date(date_str)

    # Build CSV response in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(rows)

    # Prepare Flask response with CSV data
    csv_data = output.getvalue()
    output.close()

    # Return as CSV
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-disposition": f"attachment; filename=weather_{date_str}.csv"
        },
    )


# route for backward compatibility
@app.route("/api/weather_web")
def home():
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    today = datetime.date.today().strftime("%Y-%m-%d")

    cur_weather = weather_db.get_last_record()[0]
    last_reading = cur_weather[1]
    cur_temp = cur_weather[2]
    cur_rh = cur_weather[3]
    cur_cpu_temp = cur_weather[4]
    cur_wind_speed = cur_weather[5]
    cur_wind_dir = cur_weather[6]
    cur_rain_qty = cur_weather[7]

    ds = weather_db.get_daily_summary(today)
    
    return f"""
    <html>
    <head>
        <title>Weather Data</title>
    </head>
    <body>
        <h1>Current Weather Data</h1>
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
