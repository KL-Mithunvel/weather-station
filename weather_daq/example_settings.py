import board

ACQUIRE_INTERVAL = 60    # seconds
DHT_RETRY_COUNT = 3
DHT_RECOVERY_INTERVAL = 3
DHT_READINGS_BUFFER_SIZE = 10

DB_SETTINGS = {
    'DB_HOST': "",
    'DB_PORT': "",
    'DB_USER': "",
    'DB_PASSWD': "",
    'DB_NAME': "",
    'DB_FILE_NAME':'/home/klm/weather/data/weather_data.db'
}
DHT_PIN = board.D4
WIND_SPEED_PIN = None
WIND_DIR_PIN = None
RAIN_PIN = None

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200