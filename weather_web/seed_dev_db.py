"""Generate a local dev database with 48 hours of realistic weather data."""
import math
import random
import sqlite3
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weather_dev.db')


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP,
            temp REAL, rh REAL, cpu_temp REAL,
            wind_speed REAL, wind_dir INTEGER, rain_qty REAL
        )
    """)
    conn.execute("DELETE FROM weather")

    now = datetime.datetime.now().replace(second=0, microsecond=0)
    start = now - datetime.timedelta(hours=48)
    records = []
    t = start
    random.seed(42)

    while t <= now:
        h = t.hour + t.minute / 60.0
        # Temperature: peak ~14:00, trough ~04:00, typical Tamil Nadu May
        temp = 34 + 6 * math.sin((h - 4) * math.pi / 10 - math.pi / 2)
        temp = round(max(27.0, min(44.0, temp + random.gauss(0, 0.4))), 1)

        # Humidity: inverse of temperature
        rh = 80 - 22 * math.sin((h - 4) * math.pi / 10 - math.pi / 2)
        rh = round(max(40.0, min(95.0, rh + random.gauss(0, 2))), 1)

        # Wind: mostly south-westerly (225°), light to moderate
        wind_speed = round(max(0.0, min(45.0, abs(random.gauss(10, 5)))), 1)
        wind_dir = int((225 + random.gauss(0, 35)) % 360)

        # Rain: rare bursts
        rain_qty = 0.0
        if random.random() < 0.015:
            rain_qty = round(random.uniform(0.28, 1.4), 2)

        # CPU temp: loosely follows ambient
        cpu_temp = round(max(40.0, min(82.0, 52 + (temp - 34) * 0.6 + random.gauss(0, 1.5))), 1)

        records.append((
            t.strftime('%Y-%m-%d %H:%M:%S'),
            temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty
        ))
        t += datetime.timedelta(minutes=1)

    conn.executemany(
        "INSERT INTO weather (timestamp, temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty) VALUES (?,?,?,?,?,?,?)",
        records
    )
    conn.commit()
    conn.close()
    print(f"Seeded {len(records)} records into {DB_PATH}")


if __name__ == '__main__':
    seed()