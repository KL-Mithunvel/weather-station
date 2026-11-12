"""Sensirion SHT4x (SHT40/41/43/45) temperature + humidity over I2C.

Drop-in replacement for dht_sensor.DHTSensor: acquire.py only uses read_values(),
is_faulty, last_error, readings_are_repeating(), recover_sensor(), close() and
status_name, all provided here. Select it with `TEMP_SENSOR = 'sht45'` in
settings.py (see example_settings.py). Imported only when selected, so the I2C
stack never loads on a station still using the DHT22.

Wiring (Pi 4): 3V3 -> VIN, GND -> GND, GPIO2/SDA (pin 3) -> SDA, GPIO3/SCL (pin 5)
-> SCL. I2C must be on (`dtparam=i2c_arm=on`, already set). Keep the cable under
~1 m; for longer runs use an RS485 sensor instead. Default address 0x44.

Needs `pip install adafruit-circuitpython-sht4x` in the DAQ venv.

Like every sensor wrapper here it owns its recovery and never raises at the
caller: a missing library, a missing chip or a bus error just produces
(None, None) and a fault the status file / web banner report.
"""

import time

import settings
from daq_log import logger

# Physical limits of the part (datasheet): beyond these a value is a bus glitch.
TEMP_RANGE = (-40.0, 125.0)
# The element can read a hair over 100 %RH in condensing air; clamp that, but
# treat anything wildly out of range as garbage.
RH_GARBAGE_ABOVE = 105.0


class SHT4xSensor:
    # Key used in the status file's `sensors` map (the DHT22 wrapper uses 'dht22').
    status_name = 'temp_rh'

    def __init__(self, i2c_addr=0x44):
        self.is_faulty = False
        self.last_error = None
        self.i2c_addr = i2c_addr
        self.i2c = None
        self.sensor = None
        self.readings = []
        self._open()

    def _open(self):
        """Open the bus and chip. Never raises - a failure is reported as a fault."""
        try:
            import adafruit_sht4x
            import board
            self.i2c = board.I2C()
            self.sensor = adafruit_sht4x.SHT4x(self.i2c, address=self.i2c_addr)
            # No heater, highest repeatability: ambient measurement.
            self.sensor.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
            self.is_faulty = False
            self.last_error = None
            logger.info(f'SHT4x opened at I2C address 0x{self.i2c_addr:02x}')
        except Exception as e:
            self.sensor = None
            self.is_faulty = True
            self.last_error = str(e) or e.__class__.__name__
            logger.error(f'SHT4x open failed: {self.last_error}')

    def close(self):
        if self.i2c is not None:
            try:
                self.i2c.deinit()
            except Exception:
                pass
        self.i2c = None
        self.sensor = None

    def read_values(self):
        retries = getattr(settings, 'DHT_RETRY_COUNT', 3)
        for attempt in range(retries):
            try:
                if self.sensor is None:
                    raise RuntimeError(self.last_error or 'SHT4x not initialised')
                temp, rh = self.sensor.measurements
                if temp is None or rh is None:
                    raise RuntimeError(f'sensor returned None (t={temp}, h={rh})')
                if not (TEMP_RANGE[0] <= temp <= TEMP_RANGE[1]) or not (-5.0 <= rh <= RH_GARBAGE_ABOVE):
                    raise RuntimeError(f'out-of-range reading (t={temp}, h={rh})')
                rh = min(max(rh, 0.0), 100.0)
                self.is_faulty = False
                self.last_error = None
                return round(temp, 2), round(rh, 2)
            except Exception as e:
                self.is_faulty = True
                self.last_error = str(e) or e.__class__.__name__
                retries_left = retries - attempt - 1
                logger.error(f'SHT4x: {self.last_error} ({retries_left} retries left)')
                if retries_left:
                    time.sleep(0.5)
        return None, None

    def readings_are_repeating(self):
        # A digital part reports failure via I2C/CRC errors; it does not freeze
        # on a stale value the way the bit-banged DHT22 can.
        return False

    def recover_sensor(self):
        logger.info('SHT4x recovery: reopening the bus...')
        self.close()
        time.sleep(1)
        self._open()


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))

    addr = getattr(settings, 'SHT4X_I2C_ADDR', 0x44)
    print(f"SHT4x live test at I2C 0x{addr:02x} - reading every 2 s (Ctrl+C to stop)")
    s = SHT4xSensor(addr)
    ok = fail = 0
    try:
        while True:
            t, h = s.read_values()
            if t is None:
                fail += 1
                print(f"  FAIL last_error={s.last_error!r}  (ok={ok} fail={fail})")
            else:
                ok += 1
                print(f"  OK   {t:.2f} C   {h:.2f} %RH   (ok={ok} fail={fail})")
            time.sleep(2)
    except KeyboardInterrupt:
        print(f"\nDone. {ok} ok, {fail} fail.")
    finally:
        s.close()
