import psycopg2
from psycopg2.extras import execute_values


class WeatherTimeScaleDB:
	def __init__(self, db_settings):
		self.conn_params = {
			"host": db_settings.get("DB_HOST", "localhost"),
			"port": db_settings.get("DB_PORT", "5432"),
			"dbname": db_settings.get("DB_NAME", "iiot"),
			"user": db_settings.get("DB_USER", "weather"),
			"password": db_settings.get("DB_PASSWORD", "<PASSWORD>")
		}
		self.connection = None
		self.connect()

	def connect(self):
		self.connection = psycopg2.connect(**self.conn_params)
		with self.connection.cursor() as cur:
			try:
				cur.execute("""
		                    CREATE TABLE IF NOT EXISTS weather
		                    (
		                        timestamp TIMESTAMPTZ,
		                        temp       REAL,
		                        rh         REAL,
		                        cpu_temp   REAL,
		                        wind_speed REAL,
		                        wind_dir   INTEGER,
		                        rain_qty   REAL
		                    );
				            """)
				cur.execute("""
			                SELECT create_hypertable('weather', 'timestamp', if_not_exists => TRUE);
			            """)
				self.connection.commit()

			except psycopg2.Error as e:
				self.connection.rollback()


	def write_record(self, weather_record):
		if not self.connection:
			print("Connection not valid.")
			return None
		with self.connection.cursor() as cur:
			try:
				cur.execute("""
		                    INSERT INTO weather (timestamp, temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty)
		                    VALUES (%s, %s, %s, %s, %s, %s, %s)
				            """, (
					            weather_record.timestamp,
					            weather_record.temp,
					            weather_record.rh,
					            weather_record.cpu_temp,
					            weather_record.wind_speed,
					            weather_record.wind_dir,
					            weather_record.rain_qty
				            ))
				self.connection.commit()
			except psycopg2.Error as e:
				self.connection.rollback()
				print(e)
		return True
