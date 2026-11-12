import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import sys, types, datetime, json
sys.path.insert(0, r"weather_web")
ws = types.ModuleType("web_settings"); ws.DB_SETTINGS = {}; sys.modules["web_settings"] = ws
import psycopg2, db_api, app as A

calls = {"n": 0, "fail": False}
now = datetime.datetime(2026, 11, 12, 12, 0, 0)
class FakeDB:
    def __init__(self, s):
        if calls["fail"]: raise psycopg2.OperationalError("connection refused to 10.24.0.123 secret-detail")
        calls["n"] += 1
    def get_last_record(self): return [(now, 25.1, 60.0, 50.0, 3.2, 112.5, 0.0)]
    def get_daily_summary(self, d):
        return {"date": d, "temp": {"min": 20, "max": 30, "avg": 25.0}, "rh": {"min": 50, "max": 70, "avg": 60.0},
                "wind_speed": {"max": 5, "avg": 2.0}, "wind_dir": {"avg": 110.0}, "rain": {"total": 0.0},
                "cpu_temp": {"min": 40, "max": 55, "avg": 50.0}}
    def get_records_by_date(self, d): return [(now, 25.1, 60.0, 50.0, 3.2, 112, 0.0)]
    def close(self): pass
db_api.WeatherDB = FakeDB
c = A.app.test_client()
ok = True
def check(name, cond):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name)

today = datetime.date.today().isoformat()
r = c.get("/api/weather_web")
check("home 200", r.status_code == 200 and b"Current Weather Data" in r.data)
check("nbsp placeholders kept", b"&nbsp;" in r.data and b"&amp;nbsp;" not in r.data)
for h in ("Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy"):
    check("header " + h, h in r.headers)
check("no HSTS over http", "Strict-Transport-Security" not in r.headers)
check("HSTS behind https proxy", "Strict-Transport-Security" in c.get("/api/weather_web", headers={"X-Forwarded-Proto": "https"}).headers)
n = calls["n"]; c.get("/api/weather_web"); c.get("/api/weather_web")
check("cache: repeat hits cause no new DB connections", calls["n"] == n)
check("redirect /", c.get("/").status_code == 302)
check("data today 200", c.get("/api/weather_data").status_code == 200)
check("summary ok", c.get(f"/api/weather_summary/{today}").status_code == 200)
check("csv ok", c.get(f"/api/data_export/csv/{today}").headers["Content-Type"].startswith("text/csv"))
check("bad date 400", c.get("/api/weather_data/not-a-date").status_code == 400)
check("injection-ish date 400", c.get("/api/weather_summary/2026-01-01'%20OR%201=1--").status_code in (400, 404))
check("future date 400", c.get("/api/weather_data/2999-01-01").status_code == 400)
check("too-old date 400", c.get("/api/weather_data/2000-01-01").status_code == 400)
check("POST 405", c.post("/api/weather_web").status_code == 405)
check("404 plain, no stack", c.get("/nope").data == b"Not Found")
# Fault banner: sensor detail must NOT leak
import tempfile, os
f = tempfile.NamedTemporaryFile("w", delete=False, suffix=".json")
json.dump({"sensors": {"dht22": {"status": "fault", "message": "/dev/gpiomem <script>x</script>"}}}, f); f.close()
A.STATUS_FILE = f.name; A._cache.clear()
body = c.get("/api/weather_web").data
check("banner shows generic label", b"Temperature / humidity sensor" in body)
check("banner leaks no raw message", b"gpiomem" not in body and b"<script>" not in body)
# DB outage
A._cache.clear(); calls["fail"] = True
r = c.get("/api/weather_web")
check("DB down, empty cache -> 503", r.status_code == 503 and b"10.24" not in r.data and b"secret" not in r.data)
check("503 has Retry-After", "Retry-After" in r.headers)
calls["fail"] = False; c.get("/api/weather_web")          # warm cache
calls["fail"] = True
for k in list(A._cache): A._cache[k] = (A._cache[k][0] - A.CACHE_TTL - 1, A._cache[k][1])   # make entries stale
r = c.get("/api/weather_web")
check("DB down, stale cache -> served 200", r.status_code == 200 and b"Current Weather Data" in r.data)
os.unlink(f.name)
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
