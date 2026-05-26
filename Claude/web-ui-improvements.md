# Weather Station Web UI — Current State & Improvement Plan

## Current State of the Web UI

### Technology Stack
- **Framework:** Flask (Python), served via Gunicorn (3 workers) behind Nginx
- **Frontend:** No separate HTML/CSS/JS files — all UI is raw HTML strings generated inline inside `weather_web/app.py`
- **Database:** SQLite3 (`weather.db`)
- **Deployment:** Systemd service on a Raspberry Pi at Pavoorchatram, Tenkasi Dt., Tamil Nadu, India

---

### Existing Pages and Endpoints

| Route | Type | Description |
|---|---|---|
| `/` | Redirect | Redirects to `/api/weather_web` |
| `/api/weather_web` | HTML page | Main summary page (the only visible UI) |
| `/api/weather_data` | JSON API | All raw records for today |
| `/api/weather_data/<YYYY-MM-DD>` | JSON API | All raw records for a given date |
| `/api/weather_summary/<YYYY-MM-DD>` | JSON API | Aggregated daily statistics for a given date |
| `/api/data_export/csv/<YYYY-MM-DD>` | File download | CSV export of raw records for a given date |

---

### What the Main Page (`/api/weather_web`) Shows

A single unstyled HTML table with a hard-coded border. No CSS, no JavaScript, no charts.

**Table columns:** Metric | Current | Min | Max | Avg

**Table rows:**
1. Last Reading — timestamp of the most recent sensor record
2. Temperature (°C) — current + daily min / max / avg
3. Humidity (% RH) — current + daily min / max / avg
4. Wind Speed — current + daily max / avg
5. Wind Direction (degrees) — current + daily avg
6. Rain Quantity — current + daily total
7. CPU Temperature (°C) — current + daily min / max / avg

**Alert banner:** If the DHT22 sensor is reporting a fault, a red inline-styled alert is shown at the top with the error message and timestamp.

---

### Sensors and Data Collected

| Sensor | Metrics | Notes |
|---|---|---|
| DHT22 | Temperature, Relative Humidity | Fault status stored in `/tmp/dht_status.json` |
| Arduino (serial) | Wind speed, Wind direction (°), Rain quantity | Rain counter resets at midnight |
| Raspberry Pi system | CPU temperature | Read from the OS |

---

### Database Schema

**Table `weather` — raw readings (one row per interval)**
```
id          INTEGER PK AUTOINCREMENT
timestamp   TIMESTAMP
temp        REAL  (°C)
rh          REAL  (% RH)
cpu_temp    REAL  (°C)
wind_speed  REAL
wind_dir    INTEGER  (degrees)
rain_qty    REAL
```

**Table `weather_summary` — daily aggregates**
```
date            DATE
min_temp        REAL
max_temp        REAL
avg_temp        REAL
min_rh          REAL
max_rh          REAL
avg_rh          REAL
max_speed       REAL
avg_wind_speed  REAL
avg_wind_dir    INTEGER
total_rain_qty  REAL
```

---

### Known Gaps (noted in README)
> "Single page web app for displaying all data and graphs — **pending**"

---

## Improvement Plan

### Goals
1. Make the interface immediately readable on any device (phone, tablet, desktop)
2. Show data visually — trends matter more than raw numbers
3. Let the user explore history without needing to know API URLs
4. Keep the sensor health status visible at all times
5. Make the data feel live — auto-refresh without a full page reload

---

### Phase 1 — Foundation (structure and look)

**Move HTML out of Python**
- Create a proper `templates/` folder and use Jinja2 templates
- Create a `static/` folder for CSS and JS
- This keeps Python code clean and makes the UI easy to edit independently

**Responsive layout**
- Use a lightweight CSS framework (e.g. Pico CSS or plain CSS Grid/Flexbox) so the page works well on mobile
- No heavy dependencies like Bootstrap unless the team prefers it

**Page sections to create**
1. Header bar — station name, location, last-updated time, live indicator dot
2. Current conditions cards — one card per metric (temp, humidity, wind speed, wind dir, rain, CPU temp)
3. Daily summary strip — min/max/avg for the day in a compact row
4. Charts section — time-series graphs for the day
5. History browser — date picker to load past days
6. Footer — sensor status and system info

---

### Phase 2 — Richer Data Display

**Current conditions cards**
Each card should show:
- Metric name and icon (thermometer, droplet, wind arrow, etc.)
- Current value in large text
- Daily min and max as small secondary text
- A subtle colour that changes with value (e.g. temperature card shifts from blue → orange → red)

**Wind direction**
- Replace raw degree number with a compass rose or a directional arrow graphic
- Show the cardinal/intercardinal label (N, NNE, NE, …)

**Rain**
- Show today's total prominently
- Add a small bar indicating how today's rain compares to a rolling 7-day or 30-day average

**Sensor fault banner**
- Keep the DHT22 error alert but style it properly (sticky top bar, dismissible)
- Extend it to show which sensor is faulty, since the system may add more sensors later

---

### Phase 3 — Charts and Trends

Use a lightweight charting library (Chart.js is the most practical — small, no build step needed).

**Charts to add (all time-series for the selected day)**

| Chart | Y-axis | Notes |
|---|---|---|
| Temperature | °C | Line chart |
| Humidity | % RH | Line chart, same x-axis as temp (overlay or stacked) |
| Wind Speed | raw units | Line chart with max gust highlighted |
| Wind Direction | 0–360° | Scatter or polar area chart |
| Rain accumulation | cumulative total | Step/area chart that only ever goes up during the day |
| CPU Temperature | °C | Line chart (can be hidden by default) |

**Chart interactions**
- Hover tooltip showing exact value and timestamp
- Click a point to highlight the raw reading in a detail panel
- Zoom/pan for long days with dense data (Chart.js zoom plugin)

---

### Phase 4 — History and Navigation

**Date picker**
- Allow selecting any past date
- Load data via the existing `/api/weather_data/<date>` and `/api/weather_summary/<date>` endpoints without a page reload
- Show a "no data" state gracefully for dates before the station started

**Week and month summary view**
- A table or heatmap showing daily min/max/total for the last 7 or 30 days
- Click a row to drill into that day's charts

**CSV download button**
- Surface the existing `/api/data_export/csv/<date>` endpoint as a visible button in the UI rather than a hidden URL

---

### Phase 5 — Live Updates

**Auto-refresh**
- Poll `/api/weather_data` every 60 seconds (or whatever the sensor interval is)
- Update the current-conditions cards and append new points to the charts without reloading the page
- Show a "last updated X seconds ago" counter

**Optional: Server-Sent Events (SSE)**
- Flask supports SSE natively; this would push updates to the browser the moment a new reading is stored
- More efficient than polling if the station records data frequently

---

### Phase 6 — Nice-to-Have Extras

| Feature | Description |
|---|---|
| Dark mode | CSS `prefers-color-scheme` media query — free if the CSS is written with CSS variables |
| Feels-like temperature | Calculate heat index or wind chill from temp + RH + wind and show alongside raw temperature |
| UV / pressure | Placeholders for sensors that might be added later |
| Multi-day rain total | Running 7-day and 30-day rain totals next to today's total |
| Wind rose | Polar chart showing the distribution of wind directions over the day |
| Export to JSON | Add a JSON download button alongside CSV |
| Favicon | A small weather icon in the browser tab |
| PWA / home screen | Add a web app manifest so the page can be pinned to a phone home screen |

---

### Implementation Notes

**Keep the JSON API intact** — all new UI should consume the existing endpoints. No changes to `/api/weather_data`, `/api/weather_summary`, or `/api/data_export/csv`.

**No build tools needed** — Chart.js and any CSS framework can be loaded from a local static file (or CDN fallback). This keeps deployment simple on the Raspberry Pi.

**Progressive enhancement** — the page should still show the data table if JavaScript is disabled or fails to load, so the information is never completely inaccessible.

**Performance** — the Pi has limited CPU. Keep JS minimal; avoid frameworks that require heavy client-side rendering.
