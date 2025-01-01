
from adafruit_blinka.microcontroller.bcm283x import pin


class RainSensor:
    def __init__(self, rain_pin: pin):
        pass

    @property
    def get_rainfall(self):
        return 1


if __name__ == "__main__":
    r = RainSensor()
    print(r.get_rainfall)
