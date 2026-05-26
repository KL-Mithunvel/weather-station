# Weather Station Web UI — Current State & Improvement Plan

---

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

## Wind Direction Convention

The station uses the following degree-to-flow-direction mapping. Wind direction values stored in the database represent the direction the wind is **blowing toward** (destination direction):

| Degrees | Flow Direction | Compass Label |
|---|---|---|
| 0° | NE → SW | North (compass heading of travel) |
| 45° | E → W | NE |
| 90° | SE → NW | East |
| 135° | S → N | SE |
| 180° | SW → NE | South |
| 225° | W → E | SW |
| 270° | NW → SE | West |
| 315° | N → S | NW |

**Important:** This is a non-standard convention. Standard meteorology uses the direction wind comes *from*, not *goes to*. The UI must use this station-specific mapping for all compass displays, arrow orientations, and labels — do not convert to the meteorological standard.

**Compass display logic:**
- Draw the wind arrow pointing in the direction of the stored degree value
- Label it with both the degree number and the flow description (e.g. "315° — N→S")
- Intermediate values: interpolate to nearest entry (e.g. 22° → label as "NNE → SSW")

---

## Design Inspiration — Mission Control Aesthetic

The target visual style is a **dark-theme mission control dashboard**, inspired by space station monitoring panels:

### Key Visual Principles

| Element | Description |
|---|---|
| **Background** | Deep black (`#0a0a0f`) or very dark navy |
| **Panel borders** | Bright cyan/blue glow (`#00b4d8` or `#0096c7`) — thin 1–2px borders with a subtle box-shadow glow |
| **Panel backgrounds** | Dark charcoal cards (`#111827`) — distinct from the page background |
| **Typography** | Monospace or near-monospace for numbers (e.g. JetBrains Mono, Courier, or system monospace); clean sans-serif for labels |
| **Accent colours** | Use a 4-colour status palette (see below) |
| **Status gauges** | Vertical or horizontal bars with red → yellow → green gradient (bottom=bad, top=good) |
| **Icons** | Simple, outlined, bright-coloured SVG icons for each metric |
| **Live clock** | Visible real-time clock in the header (HH:MM:SS) |
| **Section headers** | All-caps labels above each panel, e.g. "TEMPERATURE", "WIND", "RAINFALL" |

### Status Colour Palette

| Colour | Hex | Use |
|---|---|---|
| Good / Normal | `#00e676` (bright green) | Values within expected range |
| Caution | `#ffea00` (yellow) | Values approaching limits |
| Alert | `#ff6d00` (orange) | Values near threshold |
| Critical / Fault | `#f44336` (red) | Sensor fault, out-of-range values |
| Inactive / Off | `#37474f` (dark grey) | Equipment off or unavailable |

### Layout Grid

Inspired by the control panel image, use a **CSS Grid** layout with named areas:

```
┌─────────────────────────────────────────────────────────┐
│  HEADER: Station name · Location · Live clock · Status  │
├──────────────────────────────┬──────────────────────────┤
│  CURRENT CONDITIONS          │  WIND PANEL              │
│  (temp, humidity, rain cards)│  (compass + speed gauge) │
├──────────────────────────────┴──────────────────────────┤
│  GRAPHS TAB  │  HISTORY TAB                             │
│  (see below) │  (see below)                             │
└─────────────────────────────────────────────────────────┘
```

---

## Improvement Plan

### Goals
1. Dark mission-control look that is immediately readable day or night
2. Current values displayed as status cards with colour-coded health indicators
3. Charts show the past 24 hours with min / max / avg overlays
4. Separate **History** sub-tab to browse and download any past day
5. Live auto-refresh without full page reload
6. Wind direction shown as an animated compass with the station-specific degree convention

---

### Phase 1 — Foundation

**Move HTML out of Python**
- Create `weather_web/templates/` for Jinja2 templates
- Create `weather_web/static/css/` and `weather_web/static/js/`
- Single base template (`base.html`) with the dark-theme CSS variables
- All Python routes render templates, never concatenate HTML strings

**CSS architecture**
- Use CSS custom properties (variables) for the colour palette so switching themes later is trivial
- Plain CSS Grid + Flexbox — no heavy framework
- Mobile-first: single column on phones, two columns on tablets, full grid on desktop

**Add a `/` dashboard route** that returns the main SPA page (rename the current `/api/weather_web` to just be the legacy API fallback)

---

### Phase 2 — Current Conditions Cards

One card per metric, styled like the status panels in the reference image:

**Card anatomy:**
```
┌────────────────────────┐
│ ICON   METRIC NAME     │
│                        │
│      CURRENT VALUE     │  ← large monospace number
│                        │
│  MIN ──────── MAX      │  ← small secondary row
│       AVG              │
│  [status colour bar]   │  ← gauge strip at bottom
└────────────────────────┘
```

**Cards to implement:**

| Card | Icon | Colour trigger | Gauge range |
|---|---|---|---|
| Temperature | Thermometer | Blue→green→orange→red based on °C | Site-specific min/max |
| Humidity | Droplet | Green when 40–70%, yellow outside, red at extremes | 0–100% |
| Wind Speed | Arrow/fan | Green→yellow→red as speed increases | 0–max recorded |
| Wind Direction | Compass rose | Rotates to show direction; no colour coding | N/A |
| Rain Today | Rain cloud | Blue intensity increases with quantity | 0–daily max |
| CPU Temp | Chip | Green→yellow→red | 0–85°C (Pi limit) |

**Wind Direction Card (special)**
- Animated SVG compass rose
- Arrow rotates to the stored degree value
- Shows degree number + flow label using the station convention table above
- e.g. "315° · N→S · NW"

---

### Phase 3 — Graphs Tab (Default Tab)

**Graphs show the past 24 hours** of raw readings, not just "today".
The x-axis always spans `now - 24h` to `now`, scrolling with time.

**Chart library:** Chart.js (loaded from local static file, CDN fallback)

**Charts to implement:**

| Chart | Type | Y-axis | Extra overlays |
|---|---|---|---|
| Temperature | Line | °C | Dashed horizontal lines for daily min, max, avg |
| Humidity | Line | % RH | Dashed lines for daily min, max, avg |
| Wind Speed | Line + bar | speed units | Bar for each reading; line for rolling avg; dot for max gust |
| Wind Direction | Scatter | 0–360° | Points coloured by speed; compass labels on y-axis (N/NE/E…) using station convention |
| Rain Accumulation | Stepped area | cumulative mm | Resets at midnight; shaded fill |
| Temp + Humidity | Dual-axis combo | °C / % | Overlaid on one chart to show correlation |

**Min / Max / Avg overlays (on every chart)**
- Dashed coloured line for daily average (cyan)
- Thin horizontal bands marking daily min and max (faint red/blue fill)
- Tooltip on hover: exact value, timestamp, and whether it was the day's min/max

**Chart controls (small toolbar above each chart)**
- Toggle min/max/avg overlays on/off
- Zoom to last 1h / 6h / 12h / 24h
- Pan left/right through data with mouse drag or swipe

---

### Phase 4 — History Sub-Tab

The History tab lives in the same page as Graphs — switching tab does not reload the page.

**Sub-tab layout:**

```
[ GRAPHS ]  [ HISTORY ]         ← tab switcher in the panel header
```

**History tab contents:**

#### Date Navigator
- Calendar date picker (HTML `<input type="date">`, no external library needed)
- "Previous day" / "Next day" arrow buttons
- Defaults to today; shows "TODAY" badge when on current date

#### Daily Summary Table
When a date is selected, fetch `/api/weather_summary/<date>` and show:

| Metric | Min | Max | Avg | Total |
|---|---|---|---|---|
| Temperature | — | — | — | n/a |
| Humidity | — | — | — | n/a |
| Wind Speed | n/a | — | — | n/a |
| Wind Direction | n/a | n/a | — | n/a |
| Rain | n/a | n/a | n/a | — |

Each cell colour-coded with the status palette.

#### Historical Charts
Same six charts as the Graphs tab, but populated with data from the selected date via `/api/weather_data/<date>`.
Min/Max/Avg overlays automatically recalculate for the selected day.

#### Download Controls
Visible, labelled buttons — not hidden API URLs:

```
[ ↓ Download CSV for 2025-05-24 ]   [ ↓ Download JSON for 2025-05-24 ]
```

- CSV button calls existing `/api/data_export/csv/<date>`
- JSON button calls `/api/weather_data/<date>` and triggers a browser download
- Both buttons update their label when a new date is selected

#### Multi-day Range Download (stretch goal)
- "From / To" date range picker
- Triggers a new backend endpoint `/api/data_export/csv/range/<start>/<end>`
- Returns a single CSV with all records in range

---

### Phase 5 — Live Updates

**Auto-refresh every 60 seconds**
- Fetch `/api/weather_data` (today) on an interval
- Update current-conditions cards in place (no page reload)
- Append new data points to the open Graphs tab charts
- "Last updated Xs ago" counter ticking in real time in the header

**Live indicator dot**
- Blinking green dot next to the clock while data is fresh
- Turns amber if the last update was > 2 minutes ago
- Turns red with a "SENSOR OFFLINE" label if no new data for > 5 minutes

**Optional: Server-Sent Events (SSE)**
- Flask natively supports SSE via streaming responses
- More efficient than polling; push data to the browser the moment a new row is written to the DB
- Use as a future upgrade path once polling is working well

---

### Phase 6 — Sensor Health Panel

Replace the basic red text alert with a proper status panel (inspired by the "LIFE-SUPPORT EQUIPMENT" section in the reference image):

```
┌─ SENSOR STATUS ─────────────────────────────────┐
│  [●] DHT22 — Temp/Humidity    ONLINE             │
│  [●] Arduino — Wind/Rain      ONLINE             │
│  [●] CPU Temp                 ONLINE             │
│  Last system check: 14:32:01                     │
└──────────────────────────────────────────────────┘
```

- Each row has a coloured status dot (green/red/grey)
- If a sensor has a fault, the dot turns red and the error message expands inline
- Panel is always visible at the bottom of the page (or collapsible footer drawer)
- On fault, a sticky banner also appears at the top (dismissible per session)

---

### Phase 7 — Polish and Extras

| Feature | Detail |
|---|---|
| Dark theme by default | CSS variables make light mode a one-line toggle; `prefers-color-scheme` respected |
| Feels-like temperature | Heat index (temp + RH) shown as a sub-label on the temperature card |
| Wind chill | Shown when temp < 15°C and wind speed > 0 |
| Favicon | SVG weather station / sun icon in the browser tab |
| PWA manifest | `manifest.json` + service worker so the page can be pinned to a phone home screen and loads offline (cached last state) |
| Wind rose chart | Polar area chart on the Graphs tab showing directional frequency distribution for the past 24h, using the station-specific degree labels |
| 7-day rain bar chart | Small bar chart on the rain card showing the last 7 days of daily totals |
| Print / export view | A clean `@media print` stylesheet that removes chrome and prints the current conditions table neatly |

---

## Implementation Notes

**Keep the JSON API intact** — all new UI consumes existing endpoints. No breaking changes to `/api/weather_data`, `/api/weather_summary`, or `/api/data_export/csv`.

**Add one new endpoint:**
- `GET /api/weather_data/last24h` — returns all records from `now - 24 hours` to `now` across midnight boundaries (the existing endpoints are date-bounded)
- `GET /api/data_export/csv/range/<start>/<end>` — multi-day CSV for the History download feature

**No build tools** — Chart.js and CSS served as static files. No npm, webpack, or transpilation. Keeps deployment simple on the Raspberry Pi.

**Progressive enhancement** — if JS is disabled, the page falls back to a rendered server-side data table. Data is never inaccessible.

**Performance on the Pi** — avoid React/Vue/Angular. Vanilla JS + Chart.js is well within the Pi's capability. Keep the number of simultaneous open charts to three or fewer if performance is a concern.

**File structure target:**
```
weather_web/
├── app.py
├── web_settings.py
├── requirements.txt
├── templates/
│   ├── base.html          ← dark-theme shell, nav, header, footer
│   ├── dashboard.html     ← main SPA page (extends base)
│   └── error.html
├── static/
│   ├── css/
│   │   └── dashboard.css  ← CSS variables + grid layout
│   └── js/
│       ├── dashboard.js   ← card updates, live refresh loop
│       ├── charts.js      ← Chart.js setup and data loading
│       ├── history.js     ← history tab, date picker, download buttons
│       └── compass.js     ← SVG compass rose with station degree convention
└── install/
    ├── weather_web.nginx
    └── weather_web.service
```
