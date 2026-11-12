import os
import sys
import types
import datetime

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, "weather_web")
ws = types.ModuleType("web_settings")
ws.DB_SETTINGS = {}
sys.modules["web_settings"] = ws
import db_api  # noqa: E402
import app as A  # noqa: E402

now = datetime.datetime(2026, 11, 13, 2, 0, 0, 5)
ok = True


def check(n, c):
    global ok
    ok &= bool(c)
    print(("PASS " if c else "FAIL ") + n)


# --- _avg
check("_avg(None) is None", db_api._avg(None, 1) is None)
check("_avg rounds", db_api._avg(25.04, 1) == 25.0)
check("_avg(0) stays 0 (a real zero is not 'missing')", db_api._avg(0.0, 1) == 0.0)


class DownDB:
    """DHT22 down all day: temp/rh are NULL; wind and CPU are fine."""
    def __init__(self, s):
        pass

    def get_last_record(self):
        return [(now, None, None, 50.0, 0.0, 112.5, 0.0)]

    def get_daily_summary(self, d):
        return {"date": d, "temp": {"min": None, "max": None, "avg": None},
                "rh": {"min": None, "max": None, "avg": None},
                "wind_speed": {"max": 0.0, "avg": 0.0}, "wind_dir": {"avg": 110.0},
                "rain": {"total": 0.0}, "cpu_temp": {"min": 40, "max": 55, "avg": 50.0}}

    def close(self):
        pass


db_api.WeatherDB = DownDB
c = A.app.test_client()
body = c.get("/api/weather_web").data.decode()
text = " ".join(__import__("re").sub(r"<[^>]*>", " ", body).split())
check("page 200 with sensor down", "Current Weather Data" in text)
check("no literal 'None' on the page", "None" not in text)
check("temperature row shows dashes", "Temperature - - - -" in text)
check("humidity row shows dashes", "Humidity - - - -" in text)
check("a real zero wind speed still shows 0.0", "Wind Speed 0.0" in text)
check("CPU temp keeps its unit", "50.0 oC" in text)
check("no 'None oC' / '0 oC' placeholder garbage", "None oC" not in text)
check("nbsp placeholders still intact", "&nbsp;" in body and "&amp;nbsp;" not in body)
s = c.get("/api/weather_summary/" + datetime.date.today().isoformat()).get_json()
check("API summary: missing avg is null", s["temp"]["avg"] is None and s["rh"]["avg"] is None)
check("API summary: real values untouched", s["cpu_temp"]["avg"] == 50.0 and s["wind_speed"]["avg"] == 0.0)
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
