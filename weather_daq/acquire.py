"""Weather station data acquisition loop.

Once every settings.ACQUIRE_INTERVAL: read the sensors, append the reading to
the local spool, then push whatever the spool still holds to TimescaleDB.
Grafana reads TimescaleDB; the small web app reads the status file written
here.

Nothing in a cycle is allowed to stop the loop. Sensor faults, serial
drop-outs and database outages are logged, reflected in the status file and
retried on the next tick - readings keep accumulating in the spool until the
database accepts them.
"""

import json
import os
import signal
import threading
import time
from datetime import datetime

import arduino_serial
import dht_sensor
import pi_cpu_temp
import settings
from WeatherTimeScaleDB import WeatherTimeScaleDB
from daq_log import logger
from records import LightningRecord, WeatherRecord
from spool import Spool

STATUS_FILE = getattr(settings, 'STATUS_FILE', '/tmp/weather_current.json')
SPOOL_FILE = getattr(settings, 'SPOOL_FILE', '/home/klm/weather/data/spool.db')
ACQUIRE_INTERVAL = getattr(settings, 'ACQUIRE_INTERVAL', 60)
FLUSH_BATCH = getattr(settings, 'FLUSH_BATCH', 500)
LIGHTNING_ENABLED = getattr(settings, 'LIGHTNING_ENABLED', False)

# One "still alive" line per this many cycles, so the log shows progress
# without writing a line a minute.
WATCHDOG_EVERY = 30

_running = True
# Wakes the between-cycles wait so a stop does not sit out the rest of the
# interval - systemd gives up and SIGKILLs after TimeoutStopSec, which matters
# for the daily reboot.
_stop = threading.Event()


def _request_stop(signum, _frame):
    global _running
    logger.info(f'Signal {signum} received, finishing current cycle then stopping.')
    _running = False
    _stop.set()


def read_sensors(dht, arduino, cpu):
    """Build one reading. Each sensor failure degrades to None, never raises."""
    rec = WeatherRecord(timestamp=datetime.now().replace(microsecond=0))

    try:
        rec.temp, rec.rh = dht.read_values()
    except Exception as e:
        logger.error(f'DHT22 read failed: {e}')

    try:
        arduino_data = arduino.read_values()
    except Exception as e:
        logger.error(f'Arduino read failed: {e}')
        arduino_data = None
    if arduino_data:
        rec.wind_dir = arduino_data['wind_dir']
        rec.wind_speed = arduino_data['wind_speed']
        rec.rain_qty = arduino_data['rain_qty']

    try:
        rec.cpu_temp = cpu.read_cpu_temp()
    except Exception as e:
        logger.error(f'CPU temperature read failed: {e}')

    return rec


def assess_health(rec, dht, arduino):
    """Per-sensor verdict for the status file, from the reading just taken."""
    health = {}

    if dht.is_faulty or rec.temp is None or rec.rh is None:
        health['dht22'] = {'status': 'fault', 'message': dht.last_error or 'No reading'}
    elif not (-40 <= rec.temp <= 80):
        health['dht22'] = {'status': 'error', 'message': f'Temperature out of range: {rec.temp} C'}
    elif not (0 <= rec.rh <= 100):
        health['dht22'] = {'status': 'error', 'message': f'Humidity out of range: {rec.rh} %'}
    else:
        health['dht22'] = {'status': 'ok', 'message': f'{rec.temp} C / {rec.rh} %RH'}

    if rec.wind_speed is None or rec.wind_dir is None:
        health['arduino'] = {'status': 'fault', 'message': arduino.last_error or 'No data from Arduino'}
    elif rec.wind_speed < 0:
        health['arduino'] = {'status': 'error', 'message': f'Negative wind speed: {rec.wind_speed}'}
    elif not (0 <= rec.wind_dir <= 360):
        health['arduino'] = {'status': 'error', 'message': f'Wind direction out of range: {rec.wind_dir}'}
    else:
        health['arduino'] = {'status': 'ok', 'message': f'{rec.wind_speed} kph / {rec.wind_dir} deg'}

    if rec.cpu_temp is None:
        health['cpu'] = {'status': 'fault', 'message': 'No CPU temperature'}
    elif rec.cpu_temp > 85:
        health['cpu'] = {'status': 'error', 'message': f'Over-temperature: {rec.cpu_temp} C'}
    else:
        health['cpu'] = {'status': 'ok', 'message': f'{rec.cpu_temp} C'}

    return health


def write_status(rec, health, pending, tdb):
    """Publish the latest reading for the web app.

    Replaced atomically so a reader never sees a half-written file.
    """
    status = dict(rec.as_dict())
    status['timestamp'] = rec.timestamp.isoformat()
    status['sensors'] = health
    status['spool_pending'] = pending
    # `connected` is only the socket. `writing` is what actually matters: a
    # connection can be open while every INSERT is rejected.
    status['timescaledb'] = {
        'connected': tdb.is_connected,
        'writing': tdb.is_connected and tdb.last_error is None,
        'last_error': tdb.last_error,
    }
    status['updated'] = datetime.now().replace(microsecond=0).isoformat()

    tmp_path = f'{STATUS_FILE}.tmp'
    try:
        os.makedirs(os.path.dirname(os.path.abspath(STATUS_FILE)), exist_ok=True)
        with open(tmp_path, 'w') as f:
            json.dump(status, f)
        os.replace(tmp_path, STATUS_FILE)
    except OSError as e:
        logger.error(f'Failed to write status file: {e}')


def flush_spool(spool, tdb):
    """Push spooled readings to TimescaleDB, dropping only what it accepted."""
    batch = spool.pending(FLUSH_BATCH)
    if not batch:
        return
    ids = [row_id for row_id, _ in batch]
    records = [record for _, record in batch]
    if tdb.write_records(records):
        spool.delete(ids)
        if len(batch) > 1:
            logger.info(f'Flushed {len(batch)} spooled readings to TimescaleDB.')


def drain_lightning(lightning, tdb):
    """Lightning events go straight to TimescaleDB; they are not spooled."""
    events = lightning.drain_events()
    if not events:
        return
    records = [LightningRecord(timestamp=e.timestamp, event_type=e.event_type,
                               distance_km=e.distance_km, energy=e.energy)
               for e in events]
    if not tdb.write_lightning_events(records):
        logger.error(f'Dropped {len(records)} lightning events - TimescaleDB unavailable.')


def date_changed():
    """True on the first cycle of a new local day, to zero the rain total."""
    today = datetime.now().date()
    if not hasattr(date_changed, 'last_date'):
        date_changed.last_date = today
        return False
    if today != date_changed.last_date:
        date_changed.last_date = today
        return True
    return False


def acquire_loop(dht, arduino, cpu, spool, tdb, lightning):
    logger.info('Begin acquire loop...')
    cycles = 0
    next_tick = time.monotonic()

    while _running:
        try:
            rec = read_sensors(dht, arduino, cpu)
            spool.add(rec)
            flush_spool(spool, tdb)

            if lightning is not None:
                drain_lightning(lightning, tdb)

            write_status(rec, assess_health(rec, dht, arduino), spool.count(), tdb)

            if date_changed():
                logger.info('New date detected. Resetting Arduino rain total...')
                arduino.reset_arduino()

            if dht.is_faulty or dht.readings_are_repeating():
                logger.error('DHT22 is in a faulty state. Recovering...')
                dht.recover_sensor()

            cycles += 1
            if cycles % WATCHDOG_EVERY == 0:
                logger.info(f'Acquire running (watchdog): {cycles} cycles, {spool.count()} spooled.')

        except Exception as e:
            # A cycle can fail for any reason; the loop has to outlive it.
            logger.error(f'Acquire cycle failed: {e}')
            logger.error('Traceback details:', exc_info=True)

        next_tick += ACQUIRE_INTERVAL
        delay = next_tick - time.monotonic()
        if delay > 0:
            _stop.wait(delay)
        else:
            # Sensor reads overran the interval; resync instead of spinning.
            next_tick = time.monotonic()


def main():
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)

    logger.info('Booting acquire loop...')
    dht = dht_sensor.DHTSensor(dht_pin=settings.DHT_PIN)
    arduino = arduino_serial.ArduinoSerial(settings.SERIAL_PORT, settings.BAUD_RATE)
    cpu = pi_cpu_temp.PiBoard()
    spool = Spool(SPOOL_FILE)
    tdb = WeatherTimeScaleDB(settings.DB_SETTINGS)
    # A failed first connect is not fatal - readings spool until it recovers.
    tdb.connect()

    lightning = None
    if LIGHTNING_ENABLED:
        # Imported only when enabled, so the AS3935 driver and its I2C stack
        # are never loaded on a station without the sensor fitted.
        import lightning_sensor
        try:
            lightning = lightning_sensor.LightningSensor(
                i2c_addr=settings.LIGHTNING_I2C_ADDR,
                irq_pin=settings.LIGHTNING_IRQ_PIN,
                i2c_bus=settings.LIGHTNING_I2C_BUS,
                outdoor=True,
            )
            lightning.start()
        except Exception as e:
            logger.error(f'Lightning sensor init failed, continuing without it: {e}')
            lightning = None
    else:
        logger.info('Lightning sensor disabled (settings.LIGHTNING_ENABLED is not set).')

    try:
        acquire_loop(dht, arduino, cpu, spool, tdb, lightning)
    finally:
        logger.info('Cleaning up acquire loop...')
        for close in (dht.close, arduino.close, spool.close, tdb.close):
            try:
                close()
            except Exception as e:
                logger.error(f'Cleanup step failed: {e}')
        if lightning is not None:
            try:
                lightning.stop()
            except Exception as e:
                logger.error(f'Lightning stop failed: {e}')
        logger.info('Acquire loop stopped.')


if __name__ == '__main__':
    main()
