# weather-station - K L Mithunvel's Weather Station

App contains three parts.
## Weather DAQ - weather_daq folder
Acquires data from sensors and stores in sqlite3 db \
* First create a venv using `python -m venv .venv`
* Install requirements: `pip install -r requirements.txt`
* Run app directly for testing: `.venv/bin/python acquire.py`. Or run as a systemd service using gunicorn for production.
* For production:
  * run as systemd service using `weather_daq.service` file 

## Weather Web - weather_web folder
Flask app for serving data and simple webpage.
* First create a venv using `python -m venv .venv`
* Install requirements: `pip install -r requirements.txt`
* Run app directly for testing: `.venv/bin/python app.py`.
* For production:
  * install nginx `sudo apt install nginx`; 
  * configure nginx by copying `weather_web.nginx` file to correct nginx folder, test config and reload nginx
  * run as a systemd service using gunicorn for production using `weather_web.service` file.

## Access URLs of flask app:
* http://ip-addr/api/weather_web - URL for viewing weather summary.
* http://ip-addr/api/data_export/csv/2025-02-20 - Download CSV for particular date

## Single page web app for displaying all data and graphs - pending
