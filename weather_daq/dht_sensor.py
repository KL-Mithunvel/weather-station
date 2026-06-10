import adafruit_dht
import board
from adafruit_blinka.microcontroller.bcm283x import pin
import time

import settings
from daq_log import logger


class DHTSensor:
    def __init__(self, dht_pin: pin):
        self.is_faulty = False
        self.last_error = None
        self.dht = None
        self.dht_pin = dht_pin
        self.readings = []
        self._open()

    def _open(self):
        # use_pulseio=False: bit-bang mode, required on Raspberry Pi (Linux).
        # The default pulseio mode tries to claim a hardware PWM resource and
        # is unreliable on Pi under libgpiod / blinka.
        self.dht = adafruit_dht.DHT22(self.dht_pin, use_pulseio=False)
        logger.info(f'DHT22 opened on pin {self.dht_pin}')
        time.sleep(1)

    def close(self):
        if self.dht is not None:
            try:
                self.dht.exit()
            except Exception:
                pass
            self.dht = None  # prevent double-exit via __del__

    def read_values(self):
        for attempt in range(settings.DHT_RETRY_COUNT):
            try:
                t = self.dht.temperature
                h = self.dht.humidity
                if t is None or h is None:
                    raise RuntimeError(f'sensor returned None (t={t}, h={h})')
                self.is_faulty = False
                self.last_error = None
                self._add_reading(t, h)
                return t, h
            except Exception as e:
                self.is_faulty = True
                self.last_error = str(e)
                retries_left = settings.DHT_RETRY_COUNT - attempt - 1
                logger.error(f'DHT22: {e} ({retries_left} retries left)')
                if retries_left:
                    time.sleep(settings.DHT_RECOVERY_INTERVAL)
        return None, None

    def _add_reading(self, temp, rh):
        self.readings.append((temp, rh))
        if len(self.readings) > settings.DHT_READINGS_BUFFER_SIZE:
            self.readings.pop(0)

    def readings_are_repeating(self):
        valid = [(t, h) for t, h in self.readings if t is not None and h is not None]
        if len(valid) < settings.DHT_READINGS_BUFFER_SIZE:
            return False
        if len(set(t for t, _ in valid)) == 1 and len(set(h for _, h in valid)) == 1:
            logger.debug('DHT22 readings repeating')
            return True
        return False

    def recover_sensor(self):
        logger.info('DHT22 recovery: restarting sensor...')
        self.close()
        self.readings = []
        time.sleep(settings.DHT_RECOVERY_INTERVAL * 2)
        self._open()


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    import settings

    pin = settings.DHT_PIN

    print("=" * 50)
    print("  DHT22 Sensor — Live Test")
    print(f"  Pin           : {pin}")
    print(f"  Retry count   : {settings.DHT_RETRY_COUNT}")
    print(f"  Recovery wait : {settings.DHT_RECOVERY_INTERVAL}s")
    print("  Reading every 2s... (Ctrl+C to stop)")
    print("=" * 50)

    s = DHTSensor(pin)
    ok = 0
    fail = 0
    try:
        while True:
            t, h = s.read_values()
            if t is not None and h is not None:
                ok += 1
                print(f"  OK   Temp: {t:.1f} °C    Humidity: {h:.1f} %RH    (ok={ok} fail={fail})")
            else:
                fail += 1
                print(f"  FAIL last_error='{s.last_error}'  (ok={ok} fail={fail})")
            time.sleep(2)
    except KeyboardInterrupt:
        print(f"\nDone. {ok} ok, {fail} fail out of {ok+fail} reads.")
    finally:
        s.close()