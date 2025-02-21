import adafruit_dht
import board
from adafruit_blinka.microcontroller.bcm283x import pin
import time

import settings
from daq_log import logger


class DHTSensor:
    def __init__(self, dht_pin: pin):
        self.is_faulty = False
        self.dht = None
        self.dht_pin = dht_pin
        self.open()
        self.readings = []

    def __del__(self):
        self.close()

    def open(self):
        self.dht = adafruit_dht.DHT22(self.dht_pin)
        logger.info('DHT22 sensor opened on pin {}'.format(self.dht_pin))
        time.sleep(1)

    def close(self):
        if self.dht:
            try:
                self.dht.exit()
            except (Exception):
                pass

    def read_values(self):
        count = settings.DHT_RETRY_COUNT
        while count > 0:
            try:
                t = self.dht.temperature
                h = self.dht.humidity
                self.is_faulty = False
                self.add_readings_to_buffer(t, h)
                return t, h
            except (Exception) as e:
                self.is_faulty = True
                count -= 1
                logger.error(
                    f'DHT22 sensor exception, retrying... ({count} retries left)'
                )
                time.sleep(settings.DHT_RECOVERY_INTERVAL)
        return None, None


    def add_readings_to_buffer(self, temp, rh):
        self.readings.append([temp, rh])
        if len(self.readings) > settings.DHT_READINGS_BUFFER_SIZE:
            self.readings.pop(0)

    def readings_are_repeating(self):
        if len(self.readings) < settings.DHT_READINGS_BUFFER_SIZE:
            return False
        if len(set([x[0] for x in self.readings])) == 1 and len(set([x[1] for x in self.readings])) == 1:
            logger.debug("Readings are repeating.")
            return True
        return False

    def recover_sensor(self):
        self.close()
        time.sleep(settings.DHT_RECOVERY_INTERVAL * 2)
        self.open()


if __name__ == "__main__":
    s = DHTSensor(board.D4)
    print(f'{s.read_temp()}oC {s.read_humidity()}%RH')
    s.close()
