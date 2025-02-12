import adafruit_dht
import board
from adafruit_blinka.microcontroller.bcm283x import pin
import sysv_ipc

RETRY_COUNT = 3


class DHTSensor:
    def __init__(self, dht_pin: pin):
        self.is_faulty = False
        self.dht = None
        self.dht_pin = dht_pin

    def open(self):
        self.dht = adafruit_dht.DHT22(self.dht_pin)

    def read_values(self):
        count = RETRY_COUNT
        while count > 0:
            self.open()
            try:
                t = self.dht.temperature
                h = self.dht.humidity
                self.close()
                return t, h
            except (RuntimeError, ValueError, OSError) as e:
                self.is_faulty = True
                count -= 1
        return None

    def read_temp(self):
        count = RETRY_COUNT
        while count > 0:
            self.open()
            try:
                t = self.dht.temperature
                self.close()
                return t
            except (RuntimeError, ValueError, OSError) as e:
                self.is_faulty = True
                count -= 1
        return None

    def read_humidity(self):
        count = RETRY_COUNT
        while count > 0:
            self.open()
            try:
                h = self.dht.humidity
                self.close()
                return h
            except RuntimeError:
                self.is_faulty = True
                count -= 1
        return None

    def close(self):
        if self.dht:
            self.dht.exit()


if __name__ == "__main__":
    s = DHTSensor(board.D4)
    print(f'{s.read_temp()}oC {s.read_humidity()}%RH')
    s.close()
