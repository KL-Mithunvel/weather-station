'use strict';

let compass       = null;
let weatherCharts = null;
let historyTab    = null;

let lastUpdateTime = null;
let alertDismissed = false;

// ── Init ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  compass       = new WeatherCompass('compass-container');
  weatherCharts = new WeatherCharts();
  historyTab    = new HistoryTab();

  setupTabs();
  tickClock();
  setInterval(tickClock, 1000);

  loadData();
  loadSensorStatus();
  setInterval(loadData, 60000);
  setInterval(loadSensorStatus, 60000);
  setInterval(tickLastUpdated, 15000);
});

// ── Clock ─────────────────────────────────────────────────
function tickClock() {
  const now = new Date();
  document.getElementById('live-clock').textContent =
    now.toLocaleTimeString('en-GB', { hour12: false });
}

function tickLastUpdated() {
  if (!lastUpdateTime) return;
  const secs = Math.round((Date.now() - lastUpdateTime) / 1000);
  let text;
  if (secs < 60)        text = secs + 's ago';
  else if (secs < 3600) text = Math.floor(secs / 60) + 'm ago';
  else                  text = Math.floor(secs / 3600) + 'h ago';
  document.getElementById('last-updated-ago').textContent = text;

  if (secs > 300)      setLiveStatus('offline');
  else if (secs > 120) setLiveStatus('stale');
}

// ── Live indicator ────────────────────────────────────────
function setLiveStatus(mode) {
  const dot  = document.getElementById('live-dot');
  const text = document.getElementById('live-status');
  dot.className = 'live-dot ' + mode;
  text.textContent = ({ ok:'LIVE', stale:'STALE', offline:'OFFLINE', error:'ERROR', connecting:'CONNECTING' })[mode] ?? mode.toUpperCase();
}

// ── Alert banner ──────────────────────────────────────────
function showAlertBanner(msg) {
  if (alertDismissed) return;
  const banner = document.getElementById('alert-banner');
  document.getElementById('alert-text').textContent = msg;
  banner.classList.remove('hidden');
}
function dismissAlert() {
  document.getElementById('alert-banner').classList.add('hidden');
  alertDismissed = true;
}
window.dismissAlert = dismissAlert;

// ── Tabs ──────────────────────────────────────────────────
function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));
      btn.classList.add('active');
      document.getElementById('tab-' + tab).classList.remove('hidden');
      if (tab === 'history') historyTab.activate();
    });
  });
}

// ── Data fetch & update ───────────────────────────────────
async function loadData() {
  setLiveStatus('connecting');
  try {
    const today = new Date().toISOString().slice(0, 10);
    const [data24h, summary] = await Promise.all([
      fetch('/api/weather_data/last24h').then(r => r.json()),
      fetch(`/api/weather_summary/${today}`).then(r => r.json()),
    ]);

    if (!data24h.length) { setLiveStatus('stale'); return; }

    lastUpdateTime = Date.now();
    setLiveStatus('ok');
    document.getElementById('last-updated-ago').textContent = 'just now';

    const latest = data24h[data24h.length - 1];
    updateCards(latest, summary);
    weatherCharts.update(data24h, summary);
  } catch (e) {
    setLiveStatus('error');
  }
}

// ── Cards ─────────────────────────────────────────────────
function fmt1(v)  { return v != null ? parseFloat(v).toFixed(1) : '--'; }
function fmt0(v)  { return v != null ? Math.round(v) : '--'; }

function setCardStatus(cardId, status) {
  const card = document.getElementById(cardId);
  if (!card) return;
  card.className = 'card status-' + (status || 'inactive');
}

function setGauge(id, value, min, max, status) {
  const bar = document.getElementById(id);
  if (!bar) return;
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
  bar.style.width = pct + '%';
  const colors = {
    ok:       '#00e676',
    caution:  '#ffea00',
    alert:    '#ff6d00',
    critical: '#f44336',
    inactive: '#37474f',
  };
  bar.style.background = colors[status] ?? '#37474f';
}

function updateCards(latest, summary) {
  const temp   = latest.temp;
  const rh     = latest.rh;
  const cpu    = latest.cpu_temp;
  const wspeed = latest.wind_speed;
  const wdir   = latest.wind_dir;
  const rain   = latest.rain_qty;
  const totalRain = summary?.rain?.total;

  // Temperature
  const tempSt = getTempStatus(temp);
  document.getElementById('cur-temp').textContent = fmt1(temp);
  document.getElementById('min-temp').textContent = fmt1(summary?.temp?.min);
  document.getElementById('avg-temp').textContent = fmt1(summary?.temp?.avg);
  document.getElementById('max-temp').textContent = fmt1(summary?.temp?.max);
  setCardStatus('card-temp', tempSt);
  setGauge('gauge-temp', temp, 15, 50, tempSt);

  // Feels-like (heat index or wind chill)
  const fl = feelsLike(temp, rh, wspeed);
  document.getElementById('feels-like').textContent = fl != null ? `Feels like ${fmt1(fl)}°C` : '';

  // Humidity
  const rhSt = getRHStatus(rh);
  document.getElementById('cur-rh').textContent  = fmt1(rh);
  document.getElementById('min-rh').textContent  = fmt1(summary?.rh?.min);
  document.getElementById('avg-rh').textContent  = fmt1(summary?.rh?.avg);
  document.getElementById('max-rh').textContent  = fmt1(summary?.rh?.max);
  setCardStatus('card-rh', rhSt);
  setGauge('gauge-rh', rh, 0, 100, rhSt);
  const dp = dewPoint(temp, rh);
  document.getElementById('dew-point').textContent = dp != null ? `Dew point ${fmt1(dp)}°C` : '';

  // Rain (show cumulative today)
  const rainSt = getRainStatus(totalRain);
  document.getElementById('cur-rain').textContent   = fmt1(totalRain);
  document.getElementById('total-rain').textContent = fmt1(totalRain);
  setCardStatus('card-rain', rainSt);
  setGauge('gauge-rain', totalRain || 0, 0, 50, rainSt);

  // CPU
  const cpuSt = getCPUStatus(cpu);
  document.getElementById('cur-cpu').textContent = fmt1(cpu);
  document.getElementById('min-cpu').textContent = fmt1(summary?.cpu_temp?.min);
  document.getElementById('avg-cpu').textContent = fmt1(summary?.cpu_temp?.avg);
  document.getElementById('max-cpu').textContent = fmt1(summary?.cpu_temp?.max);
  setCardStatus('card-cpu', cpuSt);
  setGauge('gauge-cpu', cpu, 30, 85, cpuSt);

  // Wind
  document.getElementById('cur-wind-speed').textContent = fmt1(wspeed);
  document.getElementById('max-wind-speed').textContent = fmt1(summary?.wind_speed?.max);
  document.getElementById('avg-wind-speed').textContent = fmt1(summary?.wind_speed?.avg);
  if (wdir != null) {
    compass.update(wdir);
    document.getElementById('wind-dir-label').textContent = getWindDirLabel(wdir);
  }
}

// ── Status helpers ────────────────────────────────────────
function getTempStatus(t) {
  if (t == null) return 'inactive';
  if (t > 42 || t < -10) return 'critical';
  if (t > 37) return 'alert';
  if (t > 32) return 'caution';
  return 'ok';
}
function getRHStatus(rh) {
  if (rh == null) return 'inactive';
  if (rh > 95 || rh < 15) return 'critical';
  if (rh > 85 || rh < 25) return 'alert';
  if (rh > 70 || rh < 40) return 'caution';
  return 'ok';
}
function getWindStatus(s) {
  if (s == null) return 'inactive';
  if (s > 60) return 'critical';
  if (s > 40) return 'alert';
  if (s > 20) return 'caution';
  return 'ok';
}
function getCPUStatus(t) {
  if (t == null) return 'inactive';
  if (t > 80) return 'critical';
  if (t > 70) return 'alert';
  if (t > 60) return 'caution';
  return 'ok';
}
function getRainStatus(mm) {
  if (mm == null) return 'inactive';
  if (mm > 50) return 'critical';
  if (mm > 20) return 'alert';
  if (mm > 5)  return 'caution';
  return 'ok';
}

// ── Derived values ────────────────────────────────────────
function feelsLike(temp, rh, wspeed) {
  if (temp == null) return null;
  if (temp < 15 && wspeed > 0) {
    // Wind chill
    const v = Math.pow(wspeed, 0.16);
    return 13.12 + 0.6215 * temp - 11.37 * v + 0.3965 * temp * v;
  }
  if (temp >= 27 && rh >= 40) {
    // Simplified heat index
    return -8.78469 + 1.61139411 * temp + 2.33855 * rh
           - 0.14611605 * temp * rh - 0.012308094 * temp * temp
           - 0.016424828 * rh * rh + 0.002211732 * temp * temp * rh
           + 0.00072546 * temp * rh * rh - 0.000003582 * temp * temp * rh * rh;
  }
  return null;
}

function dewPoint(temp, rh) {
  if (temp == null || rh == null || rh <= 0) return null;
  const a = 17.27, b = 237.7;
  const gamma = (a * temp) / (b + temp) + Math.log(rh / 100);
  return (b * gamma) / (a - gamma);
}

// ── Sensor status ─────────────────────────────────────────
async function loadSensorStatus() {
  try {
    const d = await fetch('/api/sensor_status').then(r => r.json());
    updateSensorPanel(d);
  } catch (e) { /* silently skip */ }
}

function updateSensorPanel(data) {
  const sensors = data.sensors || {};
  ['dht22', 'arduino', 'cpu'].forEach(key => {
    const info = sensors[key] || { status: 'unknown', message: '' };
    const dot  = document.getElementById('dot-' + key);
    const stEl = document.getElementById('status-' + key);
    const msgEl = document.getElementById('msg-' + key);

    if (dot)  dot.className  = 'sensor-dot ' + info.status;
    if (stEl) { stEl.textContent = info.status.toUpperCase(); stEl.className = 'sensor-status-text ' + info.status; }
    if (msgEl) msgEl.textContent = info.message || '';
  });

  if (data.checked_at) {
    const ts = new Date(data.checked_at);
    document.getElementById('sensor-check-time').textContent =
      ts.toLocaleTimeString('en-GB', { hour12: false });
  }

  // Raise sticky banner if any sensor is faulty/erroneous
  const faults = Object.entries(sensors)
    .filter(([, v]) => v.status === 'fault' || v.status === 'error')
    .map(([k, v]) => `${k.toUpperCase()}: ${v.message}`);
  if (faults.length && !alertDismissed) {
    showAlertBanner('⚠ Sensor fault — ' + faults.join(' | '));
  }
}