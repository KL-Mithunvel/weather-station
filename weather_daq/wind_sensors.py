from adafruit_blinka.microcontroller.bcm283x import pin


class WindSensors:
    def __init__(self, speed_pin: pin, dir_pin: pin):
        pass

    @property
    def wind_speed(self):
        return 1

    @property
    def wind_dir(self):
        return 1


if __name__ == "__main__":
    w = WindSensors(None, None)
    print(w.wind_dir, w.wind_speed)