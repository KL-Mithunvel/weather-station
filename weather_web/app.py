"""Current-readings page for the weather station.

Deliberately tiny. It reads the status file the acquire loop rewrites every
cycle - no database, no history, no charts - so a page load is one small file
read and still works when TimescaleDB is unreachable. Grafana handles history
and dashboards.
"""

import json
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template

STATUS_FILE = os.environ.get('WEATHER_STATUS_FILE', '/tmp/weather_current.json')

# A reading older than this means the acquire loop has stopped or is stuck.
STALE_AFTER_SECONDS = 180

app = Flask(__name__)


def read_status():
    """Return the DAQ status file plus a staleness verdict, or an error dict."""
    try:
        with open(STATUS_FILE) as f:
            status = json.load(f)
    except FileNotFoundError:
        return {'available': False, 'error': f'No reading yet ({STATUS_FILE} not found)'}
    except (OSError, ValueError) as e:
        return {'available': False, 'error': f'Cannot read status file: {e}'}

    # A status file written by an older DAQ has no `writing` flag; fall back to
    # the socket state so the page is right during an upgrade.
    tdb = status.get('timescaledb')
    if isinstance(tdb, dict):
        tdb.setdefault('writing', tdb.get('connected', False))

    status['available'] = True
    status['age_seconds'] = None
    status['stale'] = True
    updated = status.get('updated')
    if updated:
        try:
            age = (datetime.now() - datetime.fromisoformat(updated)).total_seconds()
            status['age_seconds'] = int(age)
            status['stale'] = age > STALE_AFTER_SECONDS
        except ValueError:
            pass
    return status


@app.template_filter('compass')
def compass_point(degrees):
    """Wind direction in degrees to a 16-point cardinal name."""
    if degrees is None:
        return ''
    points = ('N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
              'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW')
    return points[int((float(degrees) % 360) / 22.5 + 0.5) % 16]


@app.route('/')
def current():
    return render_template('current.html', status=read_status())


@app.route('/api/current')
def api_current():
    status = read_status()
    return jsonify(status), 200 if status['available'] else 503


@app.route('/healthz')
def healthz():
    """Liveness for the acquire loop, not for this app - handy for uptime checks."""
    status = read_status()
    healthy = status['available'] and not status['stale']
    return jsonify({
        'healthy': healthy,
        'age_seconds': status.get('age_seconds'),
        'checked_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }), 200 if healthy else 503


if __name__ == '__main__':
    # Debug mode enables Werkzeug's interactive debugger, which allows remote
    # code execution if reachable on the network - never bind it to 0.0.0.0.
    debug_mode = os.environ.get('FLASK_DEBUG') == '1'
    host = '127.0.0.1' if debug_mode else '0.0.0.0'
    app.run(host=host, port=8000, debug=debug_mode)
