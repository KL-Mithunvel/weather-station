from datetime import datetime
import time

import db_api
import WeatherTimeScaleDB
import pi_cpu_temp
import dht_sensor
#import wind_sensors
#import rain_sensor
import arduino_serial
import settings
from daq_log import logger


def clean_up():
    logger.info("Cleaning up acquire loop...")
    try:
        db.close()
        dht.close()
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

        if check_date_change():
            logger.debug("New date detected. Clearing Rain Value...")
            arduino.reset_arduino()

        time.sleep(settings.ACQUIRE_INTERVAL)

        if dht.is_faulty or dht.readings_are_repeating():
            logger.error("DHT is in faulty state. Recovering... ")
            dht.recover_sensor()
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
    acquire_loop()
except (Exception) as e:
    logger.error(f"Exception occurred. Exiting. \n {e}")
    clean_up()