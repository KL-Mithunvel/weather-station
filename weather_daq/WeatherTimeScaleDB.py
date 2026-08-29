"""TimescaleDB writer - the only store the weather station publishes to.

Nothing here raises at the acquire loop. Connecting is lazy and every failure
is reported as False plus a message on `last_error`, so a database that is
down or misconfigured never stops acquisition; the readings stay in the spool
until a later flush succeeds.
"""

import psycopg2
from psycopg2.extras import execute_values

from daq_log import logger

CONNECT_TIMEOUT = 5


class WeatherTimeScaleDB:

    def __init__(self, db_settings):
        self.conn_params = {
            'host': db_settings.get('DB_HOST', 'localhost'),
            'port': db_settings.get('DB_PORT', '5432'),
            'dbname': db_settings.get('DB_NAME', 'iiot'),
            'user': db_settings.get('DB_USER', 'weather'),
            'password': db_settings.get('DB_PASSWORD', ''),
        }
        self.connection = None
        self.last_error = None

    @property
    def is_connected(self):
        return self.connection is not None and not self.connection.closed

    def connect(self):
        """Open a connection and make sure the schema exists. Never raises."""
        self.close()
        logger.info(f"Connecting to TimescaleDB at {self.conn_params['host']}:{self.conn_params['port']}...")
        try:
            self.connection = psycopg2.connect(
                **self.conn_params,
                connect_timeout=CONNECT_TIMEOUT,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=3,
                application_name='weather_daq',
            )
        except psycopg2.Error as e:
            self.connection = None
            self.last_error = str(e).strip()
            logger.error(f'TimescaleDB connect failed: {self.last_error}')
            return False

        # Best-effort: the role may only hold INSERT on tables someone else
        # created, which is a perfectly good setup. A failure here is logged
        # but must not stop us writing rows.
        self._create_schema()

        self.last_error = None
        logger.info('TimescaleDB connected.')
        return True

    @staticmethod
    def _try(cur, sql, description):
        """Run a statement that is allowed to fail, inside a savepoint.

        Every schema step can legitimately fail: the role may lack CREATE on
        the schema, the table may already hold duplicate timestamps, the
        timescaledb extension may be absent. In Postgres one failed statement
        poisons the whole transaction, so each step gets a savepoint to roll
        back to and the rest still run.
        """
        cur.execute('SAVEPOINT optional_step')
        try:
            cur.execute(sql)
            cur.execute('RELEASE SAVEPOINT optional_step')
            return True
        except psycopg2.Error as e:
            cur.execute('ROLLBACK TO SAVEPOINT optional_step')
            logger.error(f'{description} skipped: {str(e).strip()}')
            return False

    def _create_schema(self):
        """Create anything missing. Every step is optional - see connect()."""
        try:
            with self.connection.cursor() as cur:
                self._try(cur, """
                    CREATE TABLE IF NOT EXISTS weather (
                        timestamp  TIMESTAMPTZ,
                        temp       REAL,
                        rh         REAL,
                        cpu_temp   REAL,
                        wind_speed REAL,
                        wind_dir   INTEGER,
                        rain_qty   REAL
                    );
                """, 'weather table')
                self._try(cur, """
                    CREATE TABLE IF NOT EXISTS lightning_strikes (
                        timestamp   TIMESTAMPTZ,
                        event_type  TEXT,
                        distance_km INTEGER,
                        energy      INTEGER
                    );
                """, 'lightning_strikes table')
                self._try(cur, "SELECT create_hypertable('weather', 'timestamp', if_not_exists => TRUE);",
                          'weather hypertable')
                self._try(cur, "SELECT create_hypertable('lightning_strikes', 'timestamp', if_not_exists => TRUE);",
                          'lightning_strikes hypertable')
                # Makes re-flushing a batch that half-succeeded a no-op instead
                # of a duplicate row, together with ON CONFLICT DO NOTHING in
                # _insert(). If the table already holds duplicate timestamps
                # this is skipped and inserts simply are not deduplicated.
                self._try(cur, 'CREATE UNIQUE INDEX IF NOT EXISTS weather_timestamp_key ON weather (timestamp);',
                          'weather timestamp unique index')
            self.connection.commit()
            return True
        except psycopg2.Error as e:
            self.connection.rollback()
            self.last_error = str(e).strip()
            logger.error(f'TimescaleDB schema setup failed: {self.last_error}')
            return False

    def _ensure_connection(self):
        if self.is_connected:
            return True
        return self.connect()

    def write_records(self, records):
        """Insert a batch of WeatherRecords in one transaction.

        Returns True only if every row was committed, so the caller can safely
        drop them from the spool.
        """
        if not records:
            return True
        return self._insert(
            'INSERT INTO weather (timestamp, temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty)'
            ' VALUES %s ON CONFLICT DO NOTHING',
            [r.as_tuple() for r in records])

    def write_lightning_events(self, records):
        if not records:
            return True
        return self._insert(
            'INSERT INTO lightning_strikes (timestamp, event_type, distance_km, energy)'
            ' VALUES %s ON CONFLICT DO NOTHING',
            [r.as_tuple() for r in records])

    def _insert(self, sql, rows):
        if not self._ensure_connection():
            return False
        try:
            with self.connection.cursor() as cur:
                execute_values(cur, sql, rows)
            self.connection.commit()
            self.last_error = None
            return True
        except psycopg2.Error as e:
            self.last_error = str(e).strip()
            logger.error(f'TimescaleDB write failed ({len(rows)} rows): {self.last_error}')
            try:
                self.connection.rollback()
            except psycopg2.Error:
                # Connection is gone; drop it so the next call reconnects.
                self.close()
            return False

    def close(self):
        if self.connection is not None:
            try:
                self.connection.close()
            except psycopg2.Error:
                pass
            self.connection = None
