from flask import Flask
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from weather_daq import db_api
import web_settings


app = Flask(__name__)

@app.route("/")
def index():
    # Get all records from the database
    weather_db = db_api.WeatherDB(web_settings.DB_SETTINGS)
    weather_db.connect()
    records = weather_db.get_last_record()

    # Build an HTML table in a simple string
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

    # Return an HTML response
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
