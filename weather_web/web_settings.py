import os

_PI_DB = '/home/klm/weather/data/weather_data.db'
_LOCAL_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weather_dev.db')

if os.environ.get('WEATHER_ENV') == 'dev' or not os.path.exists(os.path.dirname(_PI_DB)):
    _db = _LOCAL_DB
else:
    _db = _PI_DB

DB_SETTINGS = {
    "DB_FILE_NAME": _db
}