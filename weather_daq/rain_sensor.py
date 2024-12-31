

class RainSensor:
    @property
    def get_rainfall(self):
        return 1


if __name__ == "__main__":
    r = RainSensor()
    print(r.get_rainfall)
