'use strict';

class HistoryTab {
  constructor() {
    this._histCharts = {};
    this._currentDate = null;
    this._bindControls();
  }

  _bindControls() {
    const input = document.getElementById('history-date');
    const todayStr = new Date().toISOString().slice(0, 10);
    input.value = todayStr;
    this._currentDate = todayStr;

    input.addEventListener('change', () => {
      this._currentDate = input.value;
      this._load(input.value);
    });

    document.getElementById('prev-day').addEventListener('click', () => {
      const d = new Date(this._currentDate + 'T00:00:00');
      d.setDate(d.getDate() - 1);
      const s = d.toISOString().slice(0, 10);
      input.value = s;
      this._currentDate = s;
      this._load(s);
    });

    document.getElementById('next-day').addEventListener('click', () => {
      const today = new Date().toISOString().slice(0, 10);
      const d = new Date(this._currentDate + 'T00:00:00');
      d.setDate(d.getDate() + 1);
      const s = d.toISOString().slice(0, 10);
      if (s > today) return;
      input.value = s;
      this._currentDate = s;
      this._load(s);
    });
  }

  activate() {
    this._load(this._currentDate);
  }

  async _load(dateStr) {
    const summary = document.getElementById('history-summary');
    const loading = document.getElementById('history-loading');
    const empty   = document.getElementById('history-empty');
    const badge   = document.getElementById('today-badge');
    const today   = new Date().toISOString().slice(0, 10);

    summary.classList.add('hidden');
    empty.classList.add('hidden');
    loading.classList.remove('hidden');
    badge.classList.toggle('hidden', dateStr !== today);

    try {
      const [data, sum] = await Promise.all([
        fetch(`/api/weather_data/${dateStr}`).then(r => r.json()),
        fetch(`/api/weather_summary/${dateStr}`).then(r => r.json()),
      ]);

      loading.classList.add('hidden');

      if (!data.length) {
        empty.classList.remove('hidden');
        return;
      }

      this._populateSummary(dateStr, data, sum);
      this._renderCharts(dateStr, data, sum);
      this._updateDownloadLinks(dateStr, data);
      summary.classList.remove('hidden');
    } catch (e) {
      loading.classList.add('hidden');
      empty.textContent = 'Failed to load data for ' + dateStr;
      empty.classList.remove('hidden');
    }
  }

  _populateSummary(dateStr, data, sum) {
    document.getElementById('history-date-label').textContent =
      new Date(dateStr + 'T00:00:00').toLocaleDateString('en-IN', { weekday:'long', year:'numeric', month:'long', day:'numeric' });

    const fmt = v => (v != null ? parseFloat(v).toFixed(1) : '—');
    document.getElementById('h-min-temp').textContent = fmt(sum.temp?.min);
    document.getElementById('h-avg-temp').textContent = fmt(sum.temp?.avg);
    document.getElementById('h-max-temp').textContent = fmt(sum.temp?.max);
    document.getElementById('h-min-rh').textContent   = fmt(sum.rh?.min);
    document.getElementById('h-avg-rh').textContent   = fmt(sum.rh?.avg);
    document.getElementById('h-max-rh').textContent   = fmt(sum.rh?.max);
    document.getElementById('h-avg-wind').textContent = fmt(sum.wind_speed?.avg);
    document.getElementById('h-max-wind').textContent = fmt(sum.wind_speed?.max);
    document.getElementById('h-avg-dir').textContent  = sum.wind_dir?.avg != null ? Math.round(sum.wind_dir.avg) + '°' : '—';
    document.getElementById('h-total-rain').textContent = (sum.rain?.total != null ? parseFloat(sum.rain.total).toFixed(2) : '—') + ' mm';
  }

  _destroyHistCharts() {
    Object.values(this._histCharts).forEach(c => c && c.destroy());
    this._histCharts = {};
  }

  _renderCharts(dateStr, data, sum) {
    this._destroyHistCharts();

    const labels = data.map(r => r.timestamp.replace(' ', 'T'));
    const OPTS = {
      responsive: true, maintainAspectRatio: false, animation: { duration: 300 },
      plugins: {
        legend: { labels: { color: '#64748b', font: { family: 'JetBrains Mono, monospace', size: 10 }, boxWidth: 18, padding: 6 } },
        tooltip: { backgroundColor: '#0f1724', borderColor: '#00b4d8', borderWidth: 1, titleColor: '#00b4d8', bodyColor: '#e2e8f0' }
      },
      scales: {
        x: { type: 'time', time: { tooltipFormat: 'HH:mm', displayFormats: { hour: 'HH:mm' } },
             grid: { color: '#111827' }, ticks: { color: '#64748b', maxTicksLimit: 8, maxRotation: 0,
             font: { family: 'JetBrains Mono, monospace', size: 10 } } },
        y: { grid: { color: '#111827' }, ticks: { color: '#64748b', font: { family: 'JetBrains Mono, monospace', size: 10 } } }
      }
    };

    // Temperature
    const htEl = document.getElementById('hchart-temp');
    if (htEl) {
      this._histCharts.temp = new Chart(htEl, {
        type: 'line',
        data: { datasets: [
          { label: 'Temp °C', data: labels.map((l,i) => ({x:l, y:data[i].temp})),
            borderColor:'#ff8f00', backgroundColor:'rgba(255,143,0,.1)', fill:true, tension:0.3, pointRadius:1.5, borderWidth:2 },
          { label:'Min', data:labels.map(l=>({x:l, y:sum.temp?.min})), borderColor:'#1565c0', borderDash:[5,3], pointRadius:0, borderWidth:1, fill:false },
          { label:'Max', data:labels.map(l=>({x:l, y:sum.temp?.max})), borderColor:'#c62828', borderDash:[5,3], pointRadius:0, borderWidth:1, fill:false },
          { label:'Avg', data:labels.map(l=>({x:l, y:sum.temp?.avg})), borderColor:'#00e676', borderDash:[8,3], pointRadius:0, borderWidth:1.5, fill:false },
        ]},
        options: OPTS
      });
    }

    // Humidity
    const hrEl = document.getElementById('hchart-rh');
    if (hrEl) {
      this._histCharts.rh = new Chart(hrEl, {
        type: 'line',
        data: { datasets: [
          { label: 'Humidity %', data: labels.map((l,i) => ({x:l, y:data[i].rh})),
            borderColor:'#00b4d8', backgroundColor:'rgba(0,180,216,.12)', fill:true, tension:0.3, pointRadius:1.5, borderWidth:2 },
          { label:'Min', data:labels.map(l=>({x:l, y:sum.rh?.min})), borderColor:'#1565c0', borderDash:[5,3], pointRadius:0, borderWidth:1, fill:false },
          { label:'Max', data:labels.map(l=>({x:l, y:sum.rh?.max})), borderColor:'#c62828', borderDash:[5,3], pointRadius:0, borderWidth:1, fill:false },
          { label:'Avg', data:labels.map(l=>({x:l, y:sum.rh?.avg})), borderColor:'#00e676', borderDash:[8,3], pointRadius:0, borderWidth:1.5, fill:false },
        ]},
        options: { ...OPTS, scales: { ...OPTS.scales, y: { ...OPTS.scales.y, min:0, max:100 } } }
      });
    }

    // Wind Speed
    const hwEl = document.getElementById('hchart-wind-speed');
    if (hwEl) {
      this._histCharts.wind = new Chart(hwEl, {
        type: 'bar',
        data: { datasets: [
          { label: 'Wind kph', data: labels.map((l,i) => ({x:l, y:data[i].wind_speed})),
            backgroundColor:'rgba(0,180,216,.5)', borderColor:'#00b4d8', borderWidth:1 },
          { label:'Max', data:labels.map(l=>({x:l, y:sum.wind_speed?.max})), type:'line', borderColor:'#c62828', borderDash:[5,3], pointRadius:0, borderWidth:1, fill:false },
          { label:'Avg', data:labels.map(l=>({x:l, y:sum.wind_speed?.avg})), type:'line', borderColor:'#00e676', borderDash:[8,3], pointRadius:0, borderWidth:1.5, fill:false },
        ]},
        options: { ...OPTS, scales: { ...OPTS.scales, y: { ...OPTS.scales.y, min: 0 } } }
      });
    }

    // Rain accumulation
    const hrainEl = document.getElementById('hchart-rain');
    if (hrainEl) {
      let cum = 0;
      const cumData = data.map(r => { cum += (r.rain_qty || 0); return parseFloat(cum.toFixed(2)); });
      this._histCharts.rain = new Chart(hrainEl, {
        type: 'line',
        data: { datasets: [{
          label: 'Rain mm (cumulative)', data: labels.map((l,i)=>({x:l, y:cumData[i]})),
          borderColor:'#0096c7', backgroundColor:'rgba(0,150,199,.15)', fill:true, stepped:'after', pointRadius:0, borderWidth:2,
        }]},
        options: { ...OPTS, scales: { ...OPTS.scales, y: { ...OPTS.scales.y, min: 0 } } }
      });
    }
  }

  _updateDownloadLinks(dateStr, data) {
    const csvLink  = document.getElementById('dl-csv');
    const jsonLink = document.getElementById('dl-json');

    csvLink.href = `/api/data_export/csv/${dateStr}`;
    csvLink.textContent = `↓ Download CSV for ${dateStr}`;

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    jsonLink.href = URL.createObjectURL(blob);
    jsonLink.download = `weather_${dateStr}.json`;
    jsonLink.textContent = `↓ Download JSON for ${dateStr}`;
  }
}