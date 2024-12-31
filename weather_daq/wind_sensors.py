

class WindSensors:
    @property
    def wind_speed(self):
        return 1

    @property
    def wind_dir(self):
        return 1


if __name__ == "__main__":
    w = WindSensors()
    print(w.wind_dir, w.wind_speed)