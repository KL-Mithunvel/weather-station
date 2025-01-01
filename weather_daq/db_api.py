

class WeatherRecord:
    def __init__(self):
        self.timestamp = self.temp = self.rh = self.cpu_temp = self.wind_speed = self.wind_dir = self.rain_qty = None


class WeatherDB:

    def __init__(self, db_settings):
        self.connection = None

    def connect(self):
        pass

    def write_record(self, weather_record):
        pass
