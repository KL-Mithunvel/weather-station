"""
Run this file in PyCharm (or any Python 3.8+) to start the local dev server.
It will auto-install Flask if missing, seed a dev database, and open the browser.
"""
import subprocess
import sys
import os

# ── Make sure Flask is installed ──────────────────────────
try:
    import flask
except ImportError:
    print("[setup] Flask not found — installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "--quiet"])
    print("[setup] Flask installed.")

# ── Seed dev DB if it doesn't exist ──────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_dev.db")
if not os.path.exists(DB_PATH):
    print("[setup] Creating dev database with 48h of sample data...")
    import seed_dev_db
    seed_dev_db.seed()

# ── Open browser after a short delay ─────────────────────
import threading
import webbrowser
import time

def _open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000/dashboard")

threading.Thread(target=_open_browser, daemon=True).start()

# ── Start Flask ───────────────────────────────────────────
print("=" * 50)
print("  Weather Station Dev Server")
print("  http://localhost:8000/dashboard")
print("  Press Ctrl+C to stop")
print("=" * 50)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import app as weather_app
weather_app.app.run(host="127.0.0.1", port=8000, debug=False, use_reloader=False)