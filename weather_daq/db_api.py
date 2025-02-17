import sqlite3


class WeatherRecord:
    def __init__(self):
        self.timestamp = self.temp = self.rh = self.cpu_temp = self.wind_speed = self.wind_dir = self.rain_qty = None

    def __str__(self):
        return f"WeatherRecord(timestamp={self.timestamp}, temp={self.temp}, rh={self.rh}, cpu_temp={self.cpu_temp}, wind_speed={self.wind_speed}, wind_dir={self.wind_dir}, rain_qty={self.rain_qty})"


class WeatherDB:

    def __init__(self, db_settings):
        self.connection = None
        self.db_path = db_settings.get("DB_FILE_NAME", "weather.db")
        self.connect()

    def connect(self):
        self.connection = sqlite3.connect(self.db_path)
        with self.connection:
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS weather (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    temp REAL,
                    rh REAL,
                    cpu_temp REAL,
                    wind_speed REAL,
                    wind_dir INTEGER,
                    rain_qty REAL
                )
            """)
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS weather_summary (
                    date DATE,
                    min_temp REAL,
                    max_temp REAL,
                    avg_temp REAL,
                    min_rh REAL,
                    max_rh REAL,
                    avg_rh REAL,
                    max_speed REAL,
                    avg_wind_speed REAL,
                    avg_wind_dir INTEGER,
                    total_rain_qty REAL
                )
            """)


    def write_record(self, weather_record: WeatherRecord):
        if not self.connection:
            raise RuntimeError("Database connection not established")
        with self.connection:
            csql = """
                INSERT INTO weather (timestamp, temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self.connection.execute(csql, (weather_record.timestamp, weather_record.temp, weather_record.rh, weather_record.cpu_temp,
                  weather_record.wind_speed, weather_record.wind_dir, weather_record.rain_qty))
            print(weather_record)

    def get_daily_summary(self,dt):
        calc_query = """
                SELECT
                    MIN(temp) AS min_temp,
                    MAX(temp) AS max_temp,
                    AVG(temp) AS avg_temp,
                    MIN(rh)   AS min_rh,
                    MAX(rh)   AS max_rh,
                    AVG(rh)   AS avg_rh,
                    MAX(wind_speed)       AS max_speed,
                    AVG(wind_speed)       AS avg_wind_speed,
                    AVG(wind_dir)         AS avg_wind_dir,
                    SUM(rain_qty)         AS total_rain_qty
                FROM weather
                WHERE DATE(timestamp) = ?
            """

        cur = self.connection.cursor()
        cur.execute(calc_query, (dt,))
        stats = cur.fetchone()
        return stats

    def check_connection(self):
        if not self.connection:
            raise RuntimeError("Database connection not established.")

    def get_all_records(self):
        """
        Fetch all records from the 'weather' table.
        Returns a list of tuples, each representing a row:
        (id, date, temperature, humidity, wind_dir, timestamp)
        """
        self.check_connection()

        cursor = self.connection.cursor()
        cursor.execute("SELECT id, timestamp, temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty FROM weather")
        return cursor.fetchall()

    def get_records_by_date(self, dt):
        self.check_connection()
        csql = "SELECT * FROM weather WHERE DATE(timestamp) = '{}'".format(dt);

        cursor = self.connection.cursor()
        cursor.execute(csql)
        return cursor.fetchall()

    def get_last_record(self):
        self.check_connection()
        csql = "SELECT id, timestamp, temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty FROM weather ORDER BY id DESC LIMIT 1 "
        cursor = self.connection.cursor()
        cursor.execute(csql)
        return cursor.fetchall()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

