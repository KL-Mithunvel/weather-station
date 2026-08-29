"""Local write-ahead buffer for readings on their way to TimescaleDB.

Every reading is appended here first and is only deleted once TimescaleDB has
accepted it, so a database outage - bad credentials, network down, server
restart - costs disk instead of data. When the database comes back the spool
drains oldest-first and the gap backfills on its own.

This is the only thing sqlite is used for. There are no query or summary
helpers: Grafana reads TimescaleDB, and the web app reads the status file the
acquire loop writes.
"""

import os
import sqlite3
from datetime import datetime

from daq_log import logger
from records import WeatherRecord

# ~139 days at one reading a minute. The cap only matters if TimescaleDB stays
# unreachable for months; past it the oldest readings are dropped so the Pi's
# SD card cannot fill up.
DEFAULT_MAX_ROWS = 200_000


class Spool:

    def __init__(self, db_path, max_rows=DEFAULT_MAX_ROWS):
        self.db_path = db_path
        self.max_rows = max_rows
        self.connection = None
        parent = os.path.dirname(os.path.abspath(db_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.connect()

    def connect(self):
        self.connection = sqlite3.connect(self.db_path, timeout=10)
        # WAL keeps a reader from blocking the acquire loop's writes.
        self.connection.execute('PRAGMA journal_mode=WAL')
        with self.connection:
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS spool (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp  TEXT NOT NULL,
                    temp       REAL,
                    rh         REAL,
                    cpu_temp   REAL,
                    wind_speed REAL,
                    wind_dir   INTEGER,
                    rain_qty   REAL
                )
            """)
        logger.info(f'Spool ready at {self.db_path} ({self.count()} pending)')

    def add(self, record: WeatherRecord):
        """Append one reading. Raises only if the local disk is unusable."""
        with self.connection:
            self.connection.execute(
                'INSERT INTO spool (timestamp, temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                (record.timestamp.isoformat(), record.temp, record.rh, record.cpu_temp,
                 record.wind_speed, record.wind_dir, record.rain_qty))
        self._trim()

    def pending(self, limit=500):
        """Oldest-first batch of unsent readings as (id, WeatherRecord) pairs."""
        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT id, timestamp, temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty'
            ' FROM spool ORDER BY id ASC LIMIT ?', (limit,))
        batch = []
        for row in cursor.fetchall():
            batch.append((row[0], WeatherRecord(
                timestamp=datetime.fromisoformat(row[1]),
                temp=row[2], rh=row[3], cpu_temp=row[4],
                wind_speed=row[5], wind_dir=row[6], rain_qty=row[7])))
        return batch

    def delete(self, ids):
        if not ids:
            return
        with self.connection:
            self.connection.executemany('DELETE FROM spool WHERE id = ?', [(i,) for i in ids])

    def count(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM spool')
        return cursor.fetchone()[0]

    def _trim(self):
        depth = self.count()
        if depth <= self.max_rows:
            return
        excess = depth - self.max_rows
        with self.connection:
            self.connection.execute(
                'DELETE FROM spool WHERE id IN (SELECT id FROM spool ORDER BY id ASC LIMIT ?)',
                (excess,))
        logger.error(f'Spool over {self.max_rows} rows: dropped {excess} oldest readings')

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
