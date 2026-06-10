'use strict';

// Station-specific wind direction convention:
// stored degrees = direction wind is BLOWING TOWARD (destination)
const DIR_MAP = [
  { deg: 0,   label: 'N',  flow: 'NE→SW' },
  { deg: 45,  label: 'NE', flow: 'E→W'   },
  { deg: 90,  label: 'E',  flow: 'SE→NW' },
  { deg: 135, label: 'SE', flow: 'S→N'   },
  { deg: 180, label: 'S',  flow: 'SW→NE' },
  { deg: 225, label: 'SW', flow: 'W→E'   },
  { deg: 270, label: 'W',  flow: 'NW→SE' },
  { deg: 315, label: 'NW', flow: 'N→S'   },
];

function getDirInfo(degrees) {
  const norm = ((degrees % 360) + 360) % 360;
  const idx  = Math.round(norm / 45) % 8;
  return DIR_MAP[idx];
}

class WeatherCompass {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this._currentDeg = 0;
    this._svg = null;
    this._needle = null;
    this._build();
  }

  _ns(tag) { return document.createElementNS('http://www.w3.org/2000/svg', tag); }

  _build() {
    const svg = this._ns('svg');
    svg.setAttribute('viewBox', '0 0 200 200');
    svg.style.width = '100%';
    svg.style.height = '100%';

    // Background
    const bg = this._ns('circle');
    Object.assign(bg, {});
    bg.setAttribute('cx', 100); bg.setAttribute('cy', 100); bg.setAttribute('r', 92);
    bg.setAttribute('fill', '#0a0a0f');
    bg.setAttribute('stroke', '#00b4d8'); bg.setAttribute('stroke-width', '1.5');
    svg.appendChild(bg);

    // Tick marks
    for (let a = 0; a < 360; a += 22.5) {
      const rad = (a - 90) * Math.PI / 180;
      const major = a % 45 === 0;
      const r1 = major ? 76 : 82;
      const r2 = 90;
      const line = this._ns('line');
      line.setAttribute('x1', 100 + r1 * Math.cos(rad));
      line.setAttribute('y1', 100 + r1 * Math.sin(rad));
      line.setAttribute('x2', 100 + r2 * Math.cos(rad));
      line.setAttribute('y2', 100 + r2 * Math.sin(rad));
      line.setAttribute('stroke', major ? '#00b4d8' : '#0d3d4a');
      line.setAttribute('stroke-width', major ? 2 : 1);
      svg.appendChild(line);
    }

    // Cardinal labels
    const cards = [
      { label: 'N', x: 100, y: 62 },
      { label: 'E', x: 140, y: 104 },
      { label: 'S', x: 100, y: 146 },
      { label: 'W', x: 60,  y: 104 },
    ];
    cards.forEach(c => {
      const t = this._ns('text');
      t.textContent = c.label;
      t.setAttribute('x', c.x); t.setAttribute('y', c.y);
      t.setAttribute('text-anchor', 'middle');
      t.setAttribute('dominant-baseline', 'middle');
      t.setAttribute('fill', '#00b4d8');
      t.setAttribute('font-size', '13');
      t.setAttribute('font-family', 'JetBrains Mono, monospace');
      t.setAttribute('font-weight', '700');
      svg.appendChild(t);
    });

    // Intercardinal labels
    const inters = [
      { label: 'NE', x: 134, y: 66 },
      { label: 'SE', x: 134, y: 135 },
      { label: 'SW', x: 66,  y: 135 },
      { label: 'NW', x: 66,  y: 66 },
    ];
    inters.forEach(c => {
      const t = this._ns('text');
      t.textContent = c.label;
      t.setAttribute('x', c.x); t.setAttribute('y', c.y);
      t.setAttribute('text-anchor', 'middle');
      t.setAttribute('dominant-baseline', 'middle');
      t.setAttribute('fill', '#37474f');
      t.setAttribute('font-size', '9');
      t.setAttribute('font-family', 'JetBrains Mono, monospace');
      svg.appendChild(t);
    });

    // Needle group (drawn pointing UP = 0° by default)
    const needle = this._ns('g');
    needle.setAttribute('transform', 'rotate(0, 100, 100)');

    // Green head (toward stored direction)
    const head = this._ns('polygon');
    head.setAttribute('points', '100,28 94,100 106,100');
    head.setAttribute('fill', '#00e676');
    head.setAttribute('opacity', '0.95');
    needle.appendChild(head);

    // Arrowhead tip
    const tip = this._ns('polygon');
    tip.setAttribute('points', '100,20 95,38 105,38');
    tip.setAttribute('fill', '#00e676');
    needle.appendChild(tip);

    // Grey tail
    const tail = this._ns('polygon');
    tail.setAttribute('points', '100,172 94,100 106,100');
    tail.setAttribute('fill', '#37474f');
    tail.setAttribute('opacity', '0.7');
    needle.appendChild(tail);

    // Center cap
    const cap = this._ns('circle');
    cap.setAttribute('cx', 100); cap.setAttribute('cy', 100); cap.setAttribute('r', 6);
    cap.setAttribute('fill', '#00b4d8');
    needle.appendChild(cap);

    svg.appendChild(needle);
    this._needle = needle;
    this._svg = svg;
    this.container.appendChild(svg);
  }

  update(degrees) {
    if (degrees == null) return;
    this._currentDeg = degrees;
    this._needle.setAttribute('transform', `rotate(${degrees}, 100, 100)`);
  }
}

function getWindDirLabel(degrees) {
  const info     = getDirInfo(degrees);
  const fromInfo = getDirInfo((degrees + 180) % 360);
  return `${Math.round(degrees)}° · →${info.label} · from ${fromInfo.label}`;
}