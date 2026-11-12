"""Read-only query layer for the weather_web table page.

Queries TimescaleDB directly - it is the only durable store weather_daq
writes to (see weather_daq/WeatherTimeScaleDB.py). There is no local history
database on the web side.

Defence in depth for a public-facing page: every session is opened read-only
and with a statement timeout, and the date filters are range comparisons so
TimescaleDB can skip chunks instead of scanning the whole table. The real
boundary is the database role - give web_settings.DB_SETTINGS a role that only
has SELECT on `weather` (see weather.MD).
"""

import re

import psycopg2

COLS = ['timestamp', 'temp', 'rh', 'cpu_temp', 'wind_speed', 'wind_dir', 'rain_qty']

# Applied to every web session.
SESSION_OPTIONS = '-c default_transaction_read_only=on -c statement_timeout=8000 -c idle_in_transaction_session_timeout=10000'

# `timestamp >= day AND timestamp < day + 1` selects the same rows as
# `timestamp::date = day` but lets the planner prune chunks.
DAY_FILTER = "timestamp >= %(d)s::date AND timestamp < (%(d)s::date + 1)"


# Rows written by the corrected DAQ (since 2026-11-13) have a non-zero
# microsecond part; legacy rows were whole seconds. See weather_daq/acquire.py.
NEW_ERA = "(extract(microseconds from timestamp)::bigint % 1000000) <> 0"


def _session_options(db_settings):
    """SESSION_OPTIONS plus the optional DB_TIMEZONE (e.g. 'Asia/Kolkata').

    Timestamps are stored as true instants (timestamptz); the session time zone
    only decides where midnight falls and how they are displayed. The value is
    validated because it is interpolated into a connection option.
    """
    options = SESSION_OPTIONS
    tz = db_settings.get("DB_TIMEZONE")
    if tz:
        if not re.fullmatch(r"[A-Za-z0-9_+\-/]{1,64}", tz):
            raise ValueError(f"invalid DB_TIMEZONE: {tz!r}")
        options += f" -c TimeZone={tz}"
    return options


class WeatherDB:

    def __init__(self, db_settings):
        self.conn_params = {
            "host": db_settings.get("DB_HOST", "localhost"),
            "port": db_settings.get("DB_PORT", "5432"),
            "dbname": db_settings.get("DB_NAME", "iiot"),
            "user": db_settings.get("DB_USER", "weather"),
            "password": db_settings.get("DB_PASSWORD", ""),
            "connect_timeout": 5,
            "options": _session_options(db_settings),
            "application_name": "weather_web",
        }
        self.connection = None
        self.connect()

    def connect(self):
        self.connection = psycopg2.connect(**self.conn_params)

    def check_connection(self):
        if not self.connection or self.connection.closed:
            self.connect()

    def get_last_record(self):
        """Newest reading. Prefers rows of the corrected era (see NEW_ERA): until
        the legacy rows are shifted back 5h30m they sit in the same time range
        and would otherwise win "newest" and show a 5h30m-old reading."""
        self.check_connection()
        with self.connection.cursor() as cur:
            cur.execute(
                f"SELECT {', '.join(COLS)} FROM weather "
                f"WHERE timestamp > now() - INTERVAL '2 days' AND {NEW_ERA} "
                "ORDER BY timestamp DESC LIMIT 1")
            rows = cur.fetchall()
            if not rows:  # station down for 2+ days, or no new-era data yet
                cur.execute(f"SELECT {', '.join(COLS)} FROM weather ORDER BY timestamp DESC LIMIT 1")
                rows = cur.fetchall()
            return rows

    def get_records_by_date(self, dt):
        self.check_connection()
        with self.connection.cursor() as cur:
            cur.execute(
                f"SELECT {', '.join(COLS)} FROM weather WHERE {DAY_FILTER} ORDER BY timestamp",
                {"d": dt},
            )
            return cur.fetchall()

    def get_daily_summary(self, dt):
        self.check_connection()
        calc_query = f"""
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
            WHERE {DAY_FILTER}
        """
        with self.connection.cursor() as cur:
            cur.execute(calc_query, {"d": dt})
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
