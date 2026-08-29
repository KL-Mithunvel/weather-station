"""Template for the gitignored weather_daq/settings.py. Copy and fill in."""

import board

ACQUIRE_INTERVAL = 60    # seconds between readings
FLUSH_BATCH = 500        # max spooled readings pushed to TimescaleDB per cycle

DHT_PIN = board.D4
DHT_RETRY_COUNT = 3
DHT_RECOVERY_INTERVAL = 3
DHT_READINGS_BUFFER_SIZE = 10

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200

# TimescaleDB is the only store the station publishes to; Grafana reads it.
DB_SETTINGS = {
    'DB_HOST': "",
    'DB_PORT': "5432",
    'DB_USER': "",
    'DB_PASSWORD': "",
    'DB_NAME': "",
}

# Local write-ahead buffer. Readings land here first and are deleted only once
# TimescaleDB accepts them, so a database outage costs disk instead of data.
SPOOL_FILE = '/home/klm/weather/data/spool.db'

# Latest reading + sensor health, written every cycle and read by weather_web.
STATUS_FILE = '/tmp/weather_current.json'

# AS3935 lightning sensor. The driver is only imported when this is True, so
# leaving it False keeps the I2C stack out of the process entirely.
LIGHTNING_ENABLED = False
LIGHTNING_I2C_ADDR = 0x03   # default (both DIP switches ON)
LIGHTNING_I2C_BUS = 1       # /dev/i2c-1 on all modern Pis
LIGHTNING_IRQ_PIN = 17      # BCM GPIO17, physical pin 11
