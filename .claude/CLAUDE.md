# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A personal weather station in Pavoorchatram, Tenkasi Dt., TN, India. A Raspberry Pi 4B reads sensors
(DHT22 + a SparkFun Weather Meter Kit driven by an Arduino UNO) and publishes readings to
TimescaleDB. **Grafana presents history/graphs** - this repo does not. `weather_web` is a plain
current-reading + today's min/max/avg table (2026-09-14: restored the pre-graphs table UI on request,
now reading TimescaleDB directly instead of the deleted sqlite `db_api.py`). Do not reintroduce
charts, a history tab, or an SPA frontend - that's Grafana's job.

```
sensors -> weather_daq -> spool (sqlite) -> TimescaleDB -> Grafana (history/graphs, not yet installed)
                                                \-> weather_web (current reading + today's min/max/avg table, reads TimescaleDB directly, read-only)
```

## Architecture

- **`weather_daq/`** - acquisition loop (`acquire.py`), a systemd service on the Pi. Each cycle
  (`settings.ACQUIRE_INTERVAL`, default 60s) reads the sensors, appends a `WeatherRecord` to the
  spool, then flushes the spool to TimescaleDB and rewrites the status file.
  - `spool.py` - local sqlite write-ahead buffer. Readings are deleted only once TimescaleDB
    accepts them, so an outage costs disk instead of data and backfills automatically. This is the
    **only** use of sqlite; there are no query or summary helpers. Capped at 200k rows, oldest
    dropped.
  - `WeatherTimeScaleDB.py` - the only store the station publishes to. Lazy connect, batch insert
    via `execute_values`, `ON CONFLICT DO NOTHING` against a unique index on `timestamp` so a
    re-flush is idempotent. **Never raises at the caller** - failures return False and set
    `last_error`.
  - `records.py` - `WeatherRecord` / `LightningRecord` data holders.
  - Sensor wrappers own their recovery: `dht_sensor.py` (fault + repeating-reading detection),
    `arduino_serial.py` (lazy reopen on a dropped port), `pi_cpu_temp.py` (shells to `vcgencmd`).
  - **Rainfall is cumulative on the Arduino.** `arduino_serial.read_values()` returns the *delta*;
    `acquire.py` calls `reset_arduino()` at date rollover (`date_changed()`) to zero the daily total.
  - `lightning_sensor.py` (AS3935) is **kept but disabled**. It is imported only inside the
    `settings.LIGHTNING_ENABLED` branch in `acquire.py`, so the driver and its I2C stack never load
    unless the flag is set. Leave it that way unless asked.
- **`weather_web/`** - the original pre-graphs UI: one Flask page (`app.py`) rendering an inline HTML
  table (no template file, no static assets, no JS) with the current reading plus today's
  min/max/avg per field, at `/api/weather_web` (`/` redirects there). `db_api.py` here is a **new,
  read-only, TimescaleDB-backed** module (psycopg2) - not the old sqlite one, which is gone for
  good; there is no local history database on the web side. Also exposes `/api/weather_data[/<date>]`,
  `/api/weather_summary/<date>`, `/api/data_export/csv/<date>`. A sensor-fault banner reads the DAQ's
  `WEATHER_STATUS_FILE` (must match `STATUS_FILE` in DAQ settings) for `sensors.*.status` - the only
  place the two processes still share a file; everything else here is a direct TimescaleDB query.
  `weather_web/example_settings.py` - copy to `web_settings.py` (gitignored) and fill in the same
  Postgres/TimescaleDB `DB_SETTINGS` as the DAQ (a read-only DB role is a reasonable hardening step,
  not yet done).
- **`arduino UNO/DAQ.ino`** - prints `windDir,windSpeed,totalRainfall` CSV at 115200 baud once a
  second. Holds the per-vane ADC calibration table.
- **`spanner/`** - deployment scripts (Windows `.bat`).

## Reliability rules

These are the point of the current design; keep them intact when editing:

- The acquire loop must outlive any single failure. Every cycle is wrapped in `try/except`; sensor
  reads degrade to `None` rather than raising.
- Never let a database error propagate into `acquire.py`. A reading that reached the spool is safe.
- Nothing at boot may be fatal except a genuinely unusable sensor object - a failed first DB connect
  is expected and fine.
- The loop is scheduled off `time.monotonic()` so it does not drift by the sensor read time.
- SIGTERM finishes the current cycle and cleans up, so `systemctl stop` is clean.

## Database schema

TimescaleDB `weather` hypertable: `timestamp, temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty`.
`lightning_strikes` hypertable: `timestamp, event_type, distance_km, energy`. Schema is created
idempotently on connect. If you add a column, update the `CREATE TABLE`, the INSERT in
`write_records`, `records.WEATHER_FIELDS`, and the spool table + insert + `pending()` projection in
`spool.py`.

## Configuration

- `weather_daq/settings.py` and `weather_web/web_settings.py` are both **gitignored**;
  `example_settings.py` in each directory is the template. Copy and fill in.
- Both `DB_SETTINGS` dicts hold `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD` (note: `DB_PASSWORD`,
  not the old `DB_PASSWD`) and should point at the same TimescaleDB instance - `weather_web` only
  ever reads it.
- The DAQ imports the Adafruit Blinka/`board` stack, which only works on real Pi hardware. Edit here,
  run on the Pi. `spool.py`, `records.py` and `weather_web/` have no hardware dependency and *can* be
  run and tested on the Windows dev machine (as long as TimescaleDB is reachable for `weather_web`).

## Commands

```bash
# weather_daq (on the Pi)
cd weather_daq && python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python acquire.py

# weather_web (runs anywhere, needs web_settings.py filled in - see Configuration)
cd weather_web && python -m venv .venv && .venv/bin/pip install -r requirements.txt
WEATHER_STATUS_FILE=/tmp/weather_current.json .venv/bin/python app.py    # :8000
```

There is no automated test suite. `dht_sensor.py` and `pi_cpu_temp.py` have `__main__` blocks for
manual hardware checks on the Pi.

## Deployment

Raspberry Pi 4B (`rpi4b-weather`), code under `~/weather/`, production venvs named `.venv-daq` and
`.venv-web` (see the `.service` files).

```bash
cd spanner
./release.bat        # push -> Pi pulls -> restart. The real deploy.
./upload.bat         # pscp the working tree -> restart. Dev shortcut, skips git.
```

`release.bat` pushes the current branch, then runs `deploy.sh` on the Pi, which pulls,
installs requirements/systemd units **only if those files changed**, restarts and verifies.
It refuses to run with uncommitted changes. `upload.bat` bypasses git to test uncommitted
work on real hardware; it leaves the Pi's tree dirty, so the next release needs `--force`.
Neither script deletes files on the Pi. `~/weather` must be a git checkout - one-time setup
is in `weather.MD`.

Systemd units: `weather_daq/weather_daq.service`, `weather_web/install/weather_web.service`; nginx
config at `weather_web/install/weather_web.nginx`. DAQ logs go to journald and rotate daily under
`/var/log/weather/`.

## Production VM access

When asked to connect to and operate on the Pi or any production VM, follow the protocol in the
`prod-vm` skill (`.claude/skills/prod-vm/SKILL.md`): announce the connection, verify machine
identity, classify every command by tier, and log the session.
