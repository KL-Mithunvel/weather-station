# weather-station — CLAUDE.md

**Author:** K L Mithunvel (23BMH1029)  
**Location:** Pavoorchatram, Tenkasi Dt., TN, India  
**Target platform:** Raspberry Pi 4 Model B running Linux (hostname `rpi4b-weather`, user `klm`)

---

## Repository layout

```
weather-station/
├── arduino UNO/        # Arduino sketch for wind + rain sensors
│   └── DAQ.ino
├── CLAUDE/             # This documentation folder
│   └── CLAUDE.md
├── DOCS/               # Hardware datasheets
│   └── Weather_Meter_Kit_Datasheet.pdf
├── lab/                # Academic R-language lab work & data
│   ├── README.md       # DHT22 wiring guide + R statistical analysis walkthrough
│   ├── DA.md           # Digital Assistant lab (statistics in R)
│   ├── da.r / 2qn.r / rproj.r  # R scripts
│   ├── fat.md / MAT.md          # Additional lab notes
│   └── weather_2025-02-18.xlsx  # Sample dataset used in lab
├── spanner/            # Deployment helper
│   └── upload.bat      # PuTTY SCP script — copies source to Pi
├── weather_daq/        # Data acquisition service (runs on Pi)
└── weather_web/        # Flask web API + HTML summary (runs on Pi)
```

---

## Component 1 — weather_daq

### Purpose
Continuously polls sensors every 60 seconds and writes records to both a local SQLite3 database and a TimescaleDB (PostgreSQL) instance.

### Entry point
`weather_daq/acquire.py` — run directly for testing, or via systemd in production.

### Sensors
| Sensor | Interface | Module |
|--------|-----------|--------|
| DHT22 (temp + humidity) | GPIO D4 via Adafruit CircuitPython | `dht_sensor.py` |
| Wind vane + anemometer + rain gauge | Arduino UNO → USB serial `/dev/ttyACM0` @ 115200 baud | `arduino_serial.py` |
| Raspberry Pi CPU temperature | subprocess → `vcgencmd measure_temp` | `pi_cpu_temp.py` |

> `wind_sensors.py` and `rain_sensor.py` are **stubs** — they are not used in production. All wind and rain data comes from the Arduino over serial.

### Data schema (`weather` table — both SQLite and TimescaleDB)
| Column | Type | Notes |
|--------|------|-------|
| timestamp | TIMESTAMP / TIMESTAMPTZ | Second-precision |
| temp | REAL | °C from DHT22 |
| rh | REAL | % relative humidity from DHT22 |
| cpu_temp | REAL | °C from Raspberry Pi |
| wind_speed | REAL | kph from Arduino |
| wind_dir | INTEGER | degrees (0–360) from Arduino |
| rain_qty | REAL | mm, **delta** since last reading (not cumulative) |

SQLite also has a `weather_summary` table (schema defined in `db_api.py:35`).

### Configuration
Copy `example_settings.py` → `settings.py` (gitignored) and fill in values:

```python
ACQUIRE_INTERVAL = 60        # seconds between readings
DHT_PIN = board.D4           # GPIO pin for DHT22
DHT_RETRY_COUNT = 3
DHT_RECOVERY_INTERVAL = 3    # seconds between DHT retries
DHT_READINGS_BUFFER_SIZE = 10

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200

DB_SETTINGS = {
    'DB_FILE_NAME': '/home/klm/weather/data/weather_data.db',  # SQLite
    'DB_HOST': '...',   # TimescaleDB
    'DB_PORT': '5432',
    'DB_USER': '...',
    'DB_PASSWD': '...',
    'DB_NAME': '...',
}
```

### Key behaviours
- **DHT fault recovery**: if `dht.is_faulty` or readings repeat for `DHT_READINGS_BUFFER_SIZE` consecutive samples, the sensor is closed and reopened (`dht_sensor.py:65`).
- **Date-change reset**: at midnight the Arduino is reset (serial port closed and reopened) to clear the cumulative rain counter (`acquire.py:58`).
- **Rain delta**: `arduino_serial.py:31` calculates per-interval rain as `current_cumulative − last_cumulative`.
- **Watchdog log**: a heartbeat "Acquire running" message is logged every 30 iterations.

### Logging
- Path: `/var/log/weather/weather_daq.log`
- Daily rotation, 7-day retention (`daq_log.py`)
- Level: INFO (errors and above for sensor faults)

### Systemd service
File: `weather_daq/weather_daq.service`  
Working dir: `/home/klm/weather/weather_daq/`  
Interpreter: `/home/klm/weather/weather_daq/.venv-daq/bin/python acquire.py`  
Restart: on-failure, 5 s delay

### Dependencies (weather_daq)
- `Adafruit-Blinka`, `adafruit-circuitpython-dht` — DHT22 sensor
- `psycopg2` — TimescaleDB
- `pyserial` — Arduino USB serial

---

## Component 2 — weather_web

### Purpose
Flask API that reads the SQLite3 database and exposes weather data as JSON, CSV, and a simple HTML summary page.

### API endpoints
| Method | URL | Returns |
|--------|-----|---------|
| GET | `/` | Redirects to `/api/weather_web` |
| GET | `/api/weather_web` | HTML page — current reading + today's daily stats |
| GET | `/api/weather_data` | JSON array of today's raw records |
| GET | `/api/weather_data/<YYYY-MM-DD>` | JSON array of records for that date |
| GET | `/api/weather_summary/<YYYY-MM-DD>` | JSON daily summary (min/max/avg per field) |
| GET | `/api/data_export/csv/<YYYY-MM-DD>` | CSV file download for that date |

All date parameters are validated with `strptime("%Y-%m-%d")` before hitting the database.

### Configuration
`weather_web/web_settings.py`:
```python
DB_SETTINGS = {
    "DB_FILE_NAME": '/home/klm/weather/data/weather_data.db'
}
```

### Production stack
- **Gunicorn**: 3 workers, bound to `0.0.0.0:8000`
- **Nginx**: proxies port 80 → 127.0.0.1:8000 (config in `install/weather_web.nginx`)
- **Systemd**: `install/weather_web.service` — venv at `.venv-web/`

### Dependencies (weather_web)
- `Flask 3.1`, `gunicorn 23`
- `mysql-connector` (listed in requirements but not used in current code)

---

## Component 3 — Arduino UNO (DAQ.ino)

### Purpose
Reads the SparkFun Weather Meter Kit and streams CSV over USB serial to the Raspberry Pi.

### Hardware pins
| Signal | Arduino Pin |
|--------|-------------|
| Wind vane (ADC) | A0 |
| Anemometer (interrupt) | 3 |
| Rain gauge (interrupt) | 2 |

### Serial output format
One line per second at 115200 baud:
```
<wind_dir_degrees>,<wind_speed_kph>,<cumulative_rain_mm>
```
Example: `270.0,3.5,12.8`

### Calibration
- Wind vane: custom ADC lookup table matching physical sensor (16 directions, 0°–337.5°)
- Rain: 0.2794 mm per bucket tip, 100 ms debounce
- Wind speed: 2.4 kph per anemometer count per second, 1-second measurement window

### Library
`SparkFun_Weather_Meter_Kit_Arduino_Library` — must be installed in Arduino IDE.

---

## Component 4 — lab/

Academic coursework using this project's data:
- **lab/README.md**: DHT22 wiring diagram + full R walkthrough (data import, correlation, regression, z-test, t-test) using `weather_2025-02-18.xlsx`
- **lab/DA.md**: Digital Assistant 1 lab — descriptive statistics and binomial distribution in R, multiple linear regression
- R scripts (`da.r`, `2qn.r`, `rproj.r`): scratch/exercise scripts

---

## Component 5 — spanner/

`upload.bat` deploys source files to the Pi using PuTTY's `pscp`:
```bat
pscp -l klm -pw %passwd% ..\weather_daq\*.* klm@rpi4b-weather:weather/weather_daq/
pscp -l klm -pw %passwd% ..\weather_web\*.* klm@rpi4b-weather:weather/weather_web/
```
Credentials come from `secrets.bat` (gitignored — never commit passwords).

---

## Development notes

### Settings file is gitignored
`settings.py` (weather_daq) and any local credential files must not be committed. Use `example_settings.py` as the template.

### SQLite is the source of truth for the web layer
Both `weather_daq` and `weather_web` share the same SQLite file. TimescaleDB is an additional write target in the DAQ; the web app does not read from it.

### Running locally for testing
```bash
# weather_daq
cd weather_daq
python acquire.py          # needs real Pi hardware

# weather_web
cd weather_web
python app.py                          # binds 127.0.0.1:8000, debug off by default
FLASK_DEBUG=1 python app.py            # opt-in debugger, also restricted to 127.0.0.1
```
For the full dashboard experience with sample data, use `run_local.py` instead (auto-seeds dev DB, opens browser).

### Security note
- Date strings are validated before being passed to SQLite queries (`validate_date_str` in `app.py:12`, parameterised queries throughout `db_api.py`).
- Never expose raw DB credentials in settings files committed to the repo.
- `app.py`'s `__main__` block never binds the Werkzeug debugger to a non-loopback address — debug mode + `0.0.0.0` would expose remote code execution via the interactive debugger. Production always runs through gunicorn (`install/weather_web.service`), which never hits this code path.
- Unhandled exceptions are logged with full tracebacks to `/var/log/weather/weather_web.log` (rotated daily, 7-day retention — same scheme as `weather_daq`) via a global `@app.errorhandler(Exception)`, and rendered as a generic error page/JSON instead of leaking stack traces.

### Deployment path on Pi
```
/home/klm/weather/
├── data/
│   └── weather_data.db
├── weather_daq/
│   ├── .venv-daq/
│   └── *.py
└── weather_web/
    ├── .venv-web/
    └── *.py
```