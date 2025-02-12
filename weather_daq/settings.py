import board

ACQUIRE_INTERVAL = 60    # seconds

DB_SETTINGS = {
    'DB_HOST': "",
    'DB_USER': "",
    'DB_PASSWD': "",
    'DB_NAME': "",
    'DB_FILE_NAME':'/home/klm/weather/data/weather_data.db'
}

DHT_PIN = board.D4
WIND_SPEED_PIN = None
WIND_DIR_PIN = None
RAIN_PIN = None
