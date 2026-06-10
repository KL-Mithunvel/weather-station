from datetime import datetime
import json
import time

import db_api
import WeatherTimeScaleDB
import pi_cpu_temp
import dht_sensor
#import wind_sensors
#import rain_sensor
import arduino_serial
import lightning_sensor
import settings
from daq_log import logger

DHT_STATUS_FILE       = '/tmp/dht_status.json'
LIGHTNING_STATUS_FILE = '/tmp/lightning_status.json'

def write_dht_status(sensor: dht_sensor.DHTSensor):
    status = {
        'is_faulty': sensor.is_faulty,
        'last_error': sensor.last_error,
        'updated': datetime.now().replace(microsecond=0).isoformat(),
    }
    try:
        with open(DHT_STATUS_FILE, 'w') as f:
            json.dump(status, f)
    except Exception as e:
        logger.error(f'Failed to write DHT status file: {e}')


def write_lightning_status(connected: bool, error: str = None):
    status = {
        'is_connected': connected,
        'last_error': error,
        'updated': datetime.now().replace(microsecond=0).isoformat(),
    }
    try:
        with open(LIGHTNING_STATUS_FILE, 'w') as f:
            json.dump(status, f)
    except Exception as e:
        logger.error(f'Failed to write lightning status file: {e}')


def clean_up():
    logger.info("Cleaning up acquire loop...")
    try:
        db.close()
        dht.close()
        if lightning:
            lightning.stop()
    except Exception:
        pass


def check_date_change():
    current_date = datetime.now().date()

    if not hasattr(check_date_change, 'last_date'):
        check_date_change.last_date = current_date
        return False

    if current_date != check_date_change.last_date:
        check_date_change.last_date = current_date
        return True

    return False


def acquire_loop():
    run = True
    write_wd_msg = WRITE_WATCHDOG_LOG_MSG = 30
    logger.info("Begin acquire loop...")
    while run:
        rec = db_api.WeatherRecord()
        rec.timestamp = datetime.now().replace(microsecond=0)
        rec.temp, rec.rh = dht.read_values()
        write_dht_status(dht)
        arduino_data = arduino.read_values()
        if arduino_data:
            rec.wind_dir = arduino_data['wind_dir']
            rec.wind_speed = arduino_data['wind_speed']
            rec.rain_qty = arduino_data['rain_qty']
        else:
            rec.wind_speed = rec.wind_dir = rec.rain_qty = None

        rec.cpu_temp = cpu.read_cpu_temp()
        db.write_record(rec)
        tdb.write_record(rec)

        for event in (lightning.drain_events() if lightning else []):
            lr = db_api.LightningRecord()
            lr.timestamp   = event.timestamp
            lr.event_type  = event.event_type
            lr.distance_km = event.distance_km
            lr.energy      = event.energy
            db.write_lightning_event(lr)
            tdb.write_lightning_event(lr)

        if check_date_change():
            logger.debug("New date detected. Clearing Rain Value...")
            arduino.reset_arduino()

        if dht.is_faulty or dht.readings_are_repeating():
            logger.error("DHT is in faulty state. Recovering... ")
            dht.recover_sensor()

        time.sleep(settings.ACQUIRE_INTERVAL)
        write_wd_msg -= 1
        if write_wd_msg == 0:
            logger.info("Acquire running (watchdog message)...")
            write_wd_msg = WRITE_WATCHDOG_LOG_MSG

logger.info("Booting acquire loop...")
dht:dht_sensor.DHTSensor = dht_sensor.DHTSensor(dht_pin=settings.DHT_PIN)
arduino:arduino_serial.ArduinoSerial = arduino_serial.ArduinoSerial(settings.SERIAL_PORT, settings.BAUD_RATE)
cpu: pi_cpu_temp.PiBoard = pi_cpu_temp.PiBoard()
db: db_api.WeatherDB = db_api.WeatherDB(settings.DB_SETTINGS)
tdb: WeatherTimeScaleDB.WeatherTimeScaleDB = WeatherTimeScaleDB.WeatherTimeScaleDB(settings.DB_SETTINGS)
try:
    lightning: lightning_sensor.LightningSensor = lightning_sensor.LightningSensor(
        i2c_addr        = settings.LIGHTNING_I2C_ADDR,
        irq_pin         = settings.LIGHTNING_IRQ_PIN,
        i2c_bus         = settings.LIGHTNING_I2C_BUS,
        outdoor         = True,
    )
    lightning.start()
    write_lightning_status(connected=True)
except Exception as e:
    logger.error(f"Lightning sensor init failed: {e}")
    write_lightning_status(connected=False, error=str(e))
    lightning = None

try:
    acquire_loop()
except Exception as e:
    logger.error(f"Exception occurred: {e}")
    logger.error("Traceback details:", exc_info=True)
    clean_up()