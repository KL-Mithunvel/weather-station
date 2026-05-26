'use strict';

const CHART_COLORS = {
  main:    '#00b4d8',
  mainFill:'rgba(0,180,216,0.12)',
  avg:     '#00e676',
  min:     '#1565c0',
  max:     '#c62828',
  ok:      '#00e676',
  caution: '#ffea00',
  alert:   '#ff6d00',
  grid:    '#111827',
  text:    '#64748b',
};

const BASE_OPTS = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 400 },
  plugins: {
    legend: {
      labels: { color: CHART_COLORS.text, font: { family: 'JetBrains Mono, monospace', size: 10 }, boxWidth: 20, padding: 8 }
    },
    tooltip: {
      backgroundColor: '#0f1724',
      borderColor: '#00b4d8',
      borderWidth: 1,
      titleColor: '#00b4d8',
      bodyColor: '#e2e8f0',
      titleFont: { family: 'JetBrains Mono, monospace', size: 11 },
      bodyFont:  { family: 'JetBrains Mono, monospace', size: 11 },
    }
  },
  scales: {
    x: {
      type: 'time',
      time: { tooltipFormat: 'HH:mm dd-MMM', displayFormats: { hour: 'HH:mm', minute: 'HH:mm' } },
      grid: { color: CHART_COLORS.grid },
      ticks: { color: CHART_COLORS.text, maxRotation: 0, maxTicksLimit: 8,
               font: { family: 'JetBrains Mono, monospace', size: 10 } },
    },
    y: {
      grid: { color: CHART_COLORS.grid },
      ticks: { color: CHART_COLORS.text, font: { family: 'JetBrains Mono, monospace', size: 10 } },
    }
  }
};

function makeXY(records) {
  return records.map(r => ({ x: r.timestamp.replace(' ', 'T'), y: r.temp }));
}

function overlayDataset(label, value, count, color) {
  return {
    label, data: Array(count).fill(value),
    borderColor: color, borderDash: [5, 3],
    borderWidth: 1, pointRadius: 0, fill: false,
  };
}

function speedToColor(speed) {
  if (speed == null || speed <= 0)  return 'rgba(55,71,79,.6)';
  if (speed < 10)  return 'rgba(0,230,118,.7)';
  if (speed < 25)  return 'rgba(255,234,0,.7)';
  if (speed < 40)  return 'rgba(255,109,0,.7)';
  return 'rgba(244,67,54,.7)';
}

class WeatherCharts {
  constructor() {
    this.charts = {};
    this.overlays = { min: true, max: true, avg: true };
    this.hours = 24;
    this._data = [];
    this._summary = null;
    this._init();
    this._bindControls();
  }

  _init() {
    this.charts.temp      = this._makeChart('chart-temp',      this._tempConfig());
    this.charts.rh        = this._makeChart('chart-rh',        this._rhConfig());
    this.charts.windSpeed = this._makeChart('chart-wind-speed', this._windSpeedConfig());
    this.charts.windDir   = this._makeChart('chart-wind-dir',  this._windDirConfig());
    this.charts.rain      = this._makeChart('chart-rain',      this._rainConfig());
    this.charts.windRose  = this._makeWindRoseChart('chart-wind-rose');
  }

  _makeChart(id, config) {
    const el = document.getElementById(id);
    if (!el) return null;
    return new Chart(el, config);
  }

  _bindControls() {
    document.querySelectorAll('.range-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.hours = parseInt(btn.dataset.hours, 10);
        if (this._data.length) this.update(this._data, this._summary);
      });
    });
    document.querySelectorAll('.overlay-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const key = btn.dataset.overlay;
        this.overlays[key] = !this.overlays[key];
        btn.classList.toggle('off', !this.overlays[key]);
        this._applyOverlayVisibility();
      });
    });
  }

  _applyOverlayVisibility() {
    const charts = [this.charts.temp, this.charts.rh, this.charts.windSpeed];
    charts.forEach(c => {
      if (!c) return;
      // datasets: 0=main, 1=min, 2=max, 3=avg
      if (c.data.datasets[1]) c.data.datasets[1].hidden = !this.overlays.min;
      if (c.data.datasets[2]) c.data.datasets[2].hidden = !this.overlays.max;
      if (c.data.datasets[3]) c.data.datasets[3].hidden = !this.overlays.avg;
      c.update('none');
    });
  }

  _filter(data) {
    if (!data || !data.length) return [];
    const cutoff = Date.now() - this.hours * 3600 * 1000;
    return data.filter(r => {
      const ts = new Date(r.timestamp.replace(' ', 'T')).getTime();
      return ts >= cutoff;
    });
  }

  update(data, summary) {
    this._data = data;
    this._summary = summary;
    const filtered = this._filter(data);
    if (!filtered.length) return;

    const labels = filtered.map(r => r.timestamp.replace(' ', 'T'));
    const n = filtered.length;

    // Temperature
    if (this.charts.temp) {
      const temps = filtered.map(r => r.temp);
      const ds = this.charts.temp.data.datasets;
      ds[0].data = labels.map((l, i) => ({ x: l, y: temps[i] }));
      if (summary) {
        ds[1].data = labels.map(l => ({ x: l, y: summary.temp.min }));
        ds[2].data = labels.map(l => ({ x: l, y: summary.temp.max }));
        ds[3].data = labels.map(l => ({ x: l, y: summary.temp.avg }));
      }
      ds[1].hidden = !this.overlays.min;
      ds[2].hidden = !this.overlays.max;
      ds[3].hidden = !this.overlays.avg;
      this.charts.temp.update('none');
    }

    // Humidity
    if (this.charts.rh) {
      const rhs = filtered.map(r => r.rh);
      const ds = this.charts.rh.data.datasets;
      ds[0].data = labels.map((l, i) => ({ x: l, y: rhs[i] }));
      if (summary) {
        ds[1].data = labels.map(l => ({ x: l, y: summary.rh.min }));
        ds[2].data = labels.map(l => ({ x: l, y: summary.rh.max }));
        ds[3].data = labels.map(l => ({ x: l, y: summary.rh.avg }));
      }
      ds[1].hidden = !this.overlays.min;
      ds[2].hidden = !this.overlays.max;
      ds[3].hidden = !this.overlays.avg;
      this.charts.rh.update('none');
    }

    // Wind Speed
    if (this.charts.windSpeed) {
      const speeds = filtered.map(r => r.wind_speed);
      const ds = this.charts.windSpeed.data.datasets;
      ds[0].data = labels.map((l, i) => ({ x: l, y: speeds[i] }));
      if (summary) {
        ds[1].data = labels.map(l => ({ x: l, y: summary.wind_speed.max }));
        ds[2].data = labels.map(l => ({ x: l, y: summary.wind_speed.avg }));
      }
      ds[1].hidden = !this.overlays.max;
      ds[2].hidden = !this.overlays.avg;
      this.charts.windSpeed.update('none');
    }

    // Wind Direction scatter
    if (this.charts.windDir) {
      const ds = this.charts.windDir.data.datasets;
      ds[0].data = filtered.map(r => ({ x: r.timestamp.replace(' ', 'T'), y: r.wind_dir }));
      ds[0].backgroundColor = filtered.map(r => speedToColor(r.wind_speed));
      this.charts.windDir.update('none');
    }

    // Rain accumulation
    if (this.charts.rain) {
      let cum = 0;
      const cumData = filtered.map(r => { cum += (r.rain_qty || 0); return parseFloat(cum.toFixed(2)); });
      this.charts.rain.data.datasets[0].data = labels.map((l, i) => ({ x: l, y: cumData[i] }));
      this.charts.rain.update('none');
    }

    // Wind rose
    if (this.charts.windRose) {
      const bins = new Array(8).fill(0);
      filtered.forEach(r => {
        if (r.wind_speed > 0 && r.wind_dir != null) {
          const b = Math.round(((r.wind_dir % 360) + 360) % 360 / 45) % 8;
          bins[b] += 1;
        }
      });
      this.charts.windRose.data.datasets[0].data = bins;
      this.charts.windRose.update('none');
    }
  }

  // ── Config builders ───────────────────────────────────────

  _tempConfig() {
    return {
      type: 'line',
      data: { datasets: [
        { label: 'Temp °C', data: [], borderColor: '#ff8f00', backgroundColor: 'rgba(255,143,0,.1)', fill: true, tension: 0.3, pointRadius: 1.5, borderWidth: 2 },
        { label: 'Min',     data: [], borderColor: CHART_COLORS.min, borderDash:[5,3], pointRadius:0, borderWidth:1, fill:false },
        { label: 'Max',     data: [], borderColor: CHART_COLORS.max, borderDash:[5,3], pointRadius:0, borderWidth:1, fill:false },
        { label: 'Avg',     data: [], borderColor: CHART_COLORS.avg, borderDash:[8,3], pointRadius:0, borderWidth:1.5, fill:false },
      ]},
      options: { ...BASE_OPTS, scales: { ...BASE_OPTS.scales, y: { ...BASE_OPTS.scales.y, title: { display: false } } } }
    };
  }

  _rhConfig() {
    return {
      type: 'line',
      data: { datasets: [
        { label: 'Humidity %', data: [], borderColor: CHART_COLORS.main, backgroundColor: CHART_COLORS.mainFill, fill: true, tension: 0.3, pointRadius: 1.5, borderWidth: 2 },
        { label: 'Min', data: [], borderColor: CHART_COLORS.min, borderDash:[5,3], pointRadius:0, borderWidth:1, fill:false },
        { label: 'Max', data: [], borderColor: CHART_COLORS.max, borderDash:[5,3], pointRadius:0, borderWidth:1, fill:false },
        { label: 'Avg', data: [], borderColor: CHART_COLORS.avg, borderDash:[8,3], pointRadius:0, borderWidth:1.5, fill:false },
      ]},
      options: { ...BASE_OPTS, scales: { ...BASE_OPTS.scales, y: { ...BASE_OPTS.scales.y, min:0, max:100 } } }
    };
  }

  _windSpeedConfig() {
    return {
      type: 'bar',
      data: { datasets: [
        { label: 'Wind kph', data: [], backgroundColor: 'rgba(0,180,216,.5)', borderColor: CHART_COLORS.main, borderWidth: 1 },
        { label: 'Max',      data: [], type: 'line', borderColor: CHART_COLORS.max, borderDash:[5,3], pointRadius:0, borderWidth:1, fill:false },
        { label: 'Avg',      data: [], type: 'line', borderColor: CHART_COLORS.avg, borderDash:[8,3], pointRadius:0, borderWidth:1.5, fill:false },
      ]},
      options: { ...BASE_OPTS, scales: { ...BASE_OPTS.scales, y: { ...BASE_OPTS.scales.y, min: 0 } } }
    };
  }

  _windDirConfig() {
    const DIR_LABELS = ['N(NE→SW)','NE','E(SE→NW)','SE','S(SW→NE)','SW','W(NW→SE)','NW'];
    return {
      type: 'scatter',
      data: { datasets: [{
        label: 'Wind Direction',
        data: [],
        backgroundColor: [],
        pointRadius: 3,
        pointHoverRadius: 5,
      }]},
      options: {
        ...BASE_OPTS,
        scales: {
          ...BASE_OPTS.scales,
          y: {
            ...BASE_OPTS.scales.y,
            min: 0, max: 360,
            ticks: {
              ...BASE_OPTS.scales.y.ticks,
              stepSize: 45,
              callback: v => DIR_LABELS[v / 45] ?? '',
            }
          }
        },
        plugins: { ...BASE_OPTS.plugins, legend: { display: false } }
      }
    };
  }

  _rainConfig() {
    return {
      type: 'line',
      data: { datasets: [{
        label: 'Cumulative mm',
        data: [],
        borderColor: '#0096c7',
        backgroundColor: 'rgba(0,150,199,.15)',
        fill: true,
        stepped: 'after',
        pointRadius: 0,
        borderWidth: 2,
      }]},
      options: { ...BASE_OPTS, scales: { ...BASE_OPTS.scales, y: { ...BASE_OPTS.scales.y, min: 0 } } }
    };
  }

  _makeWindRoseChart(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    return new Chart(el, {
      type: 'polarArea',
      data: {
        labels: ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
        datasets: [{
          data: [0,0,0,0,0,0,0,0],
          backgroundColor: 'rgba(0,180,216,0.45)',
          borderColor: '#00b4d8',
          borderWidth: 1,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 400 },
        scales: {
          r: {
            grid: { color: CHART_COLORS.grid },
            ticks: { color: CHART_COLORS.text, backdropColor: 'transparent',
                     font: { family: 'JetBrains Mono, monospace', size: 9 } },
            pointLabels: { color: '#00b4d8', font: { family: 'JetBrains Mono, monospace', size: 10 } }
          }
        },
        plugins: { legend: { display: false }, tooltip: BASE_OPTS.plugins.tooltip }
      }
    });
  }
}