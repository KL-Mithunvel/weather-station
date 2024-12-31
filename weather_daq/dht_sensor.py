import adafruit_dht
import board


class DHTSensor:
    def __init__(self, pin):
        self.dht = adafruit_dht.DHT22(pin)

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
