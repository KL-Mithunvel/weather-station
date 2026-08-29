# weather-station - K L Mithunvel's Weather Station

A personal weather station in Pavoorchatram, Tenkasi Dt., TN, India. A Raspberry Pi 4B reads the
sensors and publishes readings to TimescaleDB. **Grafana presents the data** - this repo does not
try to.

```
sensors -> weather_daq -> local spool -> TimescaleDB -> Grafana
                       \-> status file -> weather_web (current readings only)
```

## Weather DAQ - `weather_daq/`

Reads DHT22 (temperature/humidity), a SparkFun Weather Meter Kit via an Arduino UNO (wind + rain)
and the Pi's CPU temperature once a minute.

Each reading is appended to a local sqlite **spool** and only deleted once TimescaleDB has accepted
it, so a database outage or network drop costs disk instead of data - the backlog uploads by itself
when the database comes back. Sensor faults, serial drop-outs and DB errors are logged and retried
on the next cycle; nothing stops the loop.

```bash
cd weather_daq
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp example_settings.py settings.py     # then fill in the DB credentials
.venv/bin/python acquire.py            # run directly for testing
```

Production runs it as a systemd service (`weather_daq.service`, venv named `.venv-daq`).

## Weather Web - `weather_web/`

One page showing the **current** readings and sensor health, for a quick "is it alive?" check.
It reads the status file the DAQ writes every cycle - no database, no history, no charts - so it
loads instantly and still works when TimescaleDB is unreachable.

- `/` - current readings page, refreshes every 30s
- `/api/current` - the same data as JSON
- `/healthz` - 200 if the last reading is under 3 minutes old, else 503

```bash
cd weather_web
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python app.py                # dev server on :8000
```

Production runs gunicorn behind nginx (`install/weather_web.service`, `install/weather_web.nginx`,
venv named `.venv-web`). `WEATHER_STATUS_FILE` must match `STATUS_FILE` in `weather_daq/settings.py`.

## Arduino - `arduino UNO/DAQ.ino`

Prints `windDir,windSpeed,totalRainfall` as CSV at 115200 baud once a second. Rainfall is
cumulative; the Pi records the delta and resets the board at date rollover. The per-vane ADC
calibration table lives here - edit it if wind direction reads wrong.

## Lightning sensor

`weather_daq/lightning_sensor.py` (AS3935) is kept but **disabled**. Set `LIGHTNING_ENABLED = True`
in `settings.py` to switch it on; while it is False the driver is never imported. Datasheets and
wiring notes are in `DOCS/`.

## Deployment

```bash
cd spanner && ./upload.bat     # pscp weather_daq/ and weather_web/ to the Pi
sudo systemctl restart weather_daq weather_web
```

DAQ logs go to journald and rotate daily under `/var/log/weather/`.
