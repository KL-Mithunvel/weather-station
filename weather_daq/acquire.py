from datetime import datetime
import time

import db_api
import pi_cpu_temp
import dht_sensor
import wind_sensors
import rain_sensor
import settings


def acquire_loop():
    run = True
    while run:
        rec = db_api.WeatherRecord()
        rec.timestamp = datetime.now()
        rec.temp, rec.rh = dht.read_values()
        rec.wind_dir = wind.wind_dir
        rec.wind_speed = wind.wind_speed
        rec.cpu_temp = cpu.read_cpu_temp()
        db.write_record(rec)
        time.sleep(settings.ACQUIRE_INTERVAL)


dht:dht_sensor.DHTSensor = dht_sensor.DHTSensor(dht_pin=settings.DHT_PIN)
wind:wind_sensors.WindSensors = wind_sensors.WindSensors(speed_pin=settings.WIND_SPEED_PIN,
                                                         dir_pin=settings.WIND_DIR_PIN)
rain:rain_sensor.RainSensor = rain_sensor.RainSensor(rain_pin=settings.RAIN_PIN)
cpu: pi_cpu_temp.PiBoard = pi_cpu_temp.PiBoard()
db: db_api.WeatherDB = db_api.WeatherDB(settings.DB_SETTINGS)

try:
    acquire_loop()
except (RuntimeError, OSError, ValueError) as e:
    try:
        db.close()
        dht.close()
    except Exception:
        pass
    # print(e)
