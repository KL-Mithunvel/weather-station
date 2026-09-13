"""Read-only query layer for the weather_web table page.

Queries TimescaleDB directly - it is the only durable store weather_daq
writes to now (see weather_daq/WeatherTimeScaleDB.py). There is no local
history database on the web side any more; the old sqlite-backed db_api.py
was removed when the project was pruned to a DAQ -> TimescaleDB -> Grafana
pipeline, and this module restores the old table-page query surface on top
of that pipeline instead of resurrecting sqlite.
"""

import psycopg2

COLS = ['timestamp', 'temp', 'rh', 'cpu_temp', 'wind_speed', 'wind_dir', 'rain_qty']


class WeatherDB:

    def __init__(self, db_settings):
        self.conn_params = {
            "host": db_settings.get("DB_HOST", "localhost"),
            "port": db_settings.get("DB_PORT", "5432"),
            "dbname": db_settings.get("DB_NAME", "iiot"),
            "user": db_settings.get("DB_USER", "weather"),
            "password": db_settings.get("DB_PASSWORD", ""),
            "connect_timeout": 5,
        }
        self.connection = None
        self.connect()

    def connect(self):
        self.connection = psycopg2.connect(**self.conn_params)

    def check_connection(self):
        if not self.connection or self.connection.closed:
            self.connect()

    def get_last_record(self):
        self.check_connection()
        with self.connection.cursor() as cur:
            cur.execute(f"SELECT {', '.join(COLS)} FROM weather ORDER BY timestamp DESC LIMIT 1")
            return cur.fetchall()

    def get_records_by_date(self, dt):
        self.check_connection()
        with self.connection.cursor() as cur:
            cur.execute(
                f"SELECT {', '.join(COLS)} FROM weather WHERE timestamp::date = %s::date ORDER BY timestamp",
                (dt,),
            )
            return cur.fetchall()

    def get_daily_summary(self, dt):
        self.check_connection()
        calc_query = """
            SELECT
                MIN(temp) AS min_temp,
                MAX(temp) AS max_temp,
                AVG(temp) AS avg_temp,
                MIN(rh)   AS min_rh,
                MAX(rh)   AS max_rh,
                AVG(rh)   AS avg_rh,
                MAX(wind_speed) AS max_speed,
                AVG(wind_speed) AS avg_wind_speed,
                AVG(wind_dir)   AS avg_wind_dir,
                SUM(rain_qty)   AS total_rain_qty,
                MIN(cpu_temp) AS min_cpu_temp,
                MAX(cpu_temp) AS max_cpu_temp,
                AVG(cpu_temp) AS avg_cpu_temp
            FROM weather
            WHERE timestamp::date = %s::date
        """
        with self.connection.cursor() as cur:
            cur.execute(calc_query, (dt,))
            stats = cur.fetchone()
        return {
            "date": dt,
            "temp": {"min": stats[0], "max": stats[1], "avg": round(stats[2] or 0, 1)},
            "rh": {"min": stats[3], "max": stats[4], "avg": round(stats[5] or 0, 1)},
            "wind_speed": {"max": stats[6], "avg": round(stats[7] or 0, 1)},
            "wind_dir": {"avg": round(stats[8] or 0, 0)},
            "rain": {"total": stats[9]},
            "cpu_temp": {"min": stats[10], "max": stats[11], "avg": round(stats[12] or 0, 1)},
        }

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
