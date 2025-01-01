import adafruit_dht
import board
from adafruit_blinka.microcontroller.bcm283x import pin


class DHTSensor:
    def __init__(self, dht_pin: pin):
        self.dht = adafruit_dht.DHT22(dht_pin)

    def read_temp(self):
        try:
            return self.dht.temperature
        except RuntimeError:
            return None

    def read_humidity(self):
        try:
            return self.dht.humidity
        except RuntimeError:
            return None

    def close(self):
        if self.dht:
            self.dht.exit()


if __name__ == "__main__":
    s = DHTSensor(board.D4)
    print(f'{s.read_temp()}oC {s.read_humidity()}%RH')
    s.close()
