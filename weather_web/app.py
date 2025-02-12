from flask import Flask, Response
import csv
import io
import sys
import os
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from weather_daq import db_api
import web_settings


app = Flask(__name__)

@app.route('/data/<date_str>', methods=['GET'])
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

@app.route("/weather/<date_str>", methods=["GET", "POST"])
def index(date_str=None):
    if date_str is None:
        date_str = datetime.date.today().strftime('%Y-%m-%d')
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    weather_db.connect()
    records = weather_db.get_records_by_date(date_str)

    table_html = "<table border='1' cellpadding='5' cellspacing='0'>"
    table_html += """
    <tr>
      <th>ID</th>
      <th>Timestamp</th>
      <th>Temperature</th>
      <th>Humidity</th>
      <th>CPU Temp</th>
      <th>Wind Speed</th>
      <th>Wind Dir</th>
      <th>Rain Qty</th>
    </tr>
    """

    for row in records:
        # row is a tuple: id, timestamp, temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty
        table_html += f"<tr>"
        table_html += f"<td>{row[0]}</td>"  # id
        table_html += f"<td>{row[1]}</td>"  # timestamp
        table_html += f"<td>{row[2]}</td>"  # temperature
        table_html += f"<td>{row[3]}</td>"  # humidity
        table_html += f"<td>{row[4]}</td>"  # cpu
        table_html += f"<td>{row[5]}</td>"  # wind_speed
        table_html += f"<td>{row[6]}</td>"  # wind_dir
        table_html += f"<td>{row[7]}</td>"  # rain_qty
        table_html += "</tr>"

    table_html += "</table>"

    return f"""
    <html>
    <head>
        <title>Weather Data</title>
    </head>
    <body>
        <h1>Weather Data</h1>
        {table_html}
    </body>
    </html>
    """


@app.route("/")
def home():
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    cur_weather = weather_db.get_last_record()

    return f"""
    <html>
    <head>
        <title>Weather Data</title>
    </head>
    <body>
        <h1>Current Weather Data</h1>
        {cur_weather}
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
