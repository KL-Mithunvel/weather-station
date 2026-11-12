import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import sys, datetime as dt, tempfile, os
sys.path.insert(0, "weather_daq")
from records import WeatherRecord, LightningRecord, aware
from spool import Spool
ok = True
def check(n, c):
    global ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n)

naive = dt.datetime(2026, 11, 13, 1, 53, 6)
a = aware(naive)
check("naive -> aware", a.tzinfo is not None and a.utcoffset() is not None)
check("naive treated as local wall time (same instant as .astimezone())", a == naive.astimezone())
check("wall-clock digits preserved", a.replace(tzinfo=None) == naive)
utc = dt.datetime(2026, 11, 12, 20, 23, 6, tzinfo=dt.timezone.utc)
check("aware input untouched", aware(utc) is utc)
check("None passes through", aware(None) is None)
r = WeatherRecord(timestamp=naive, temp=1.0)
check("as_tuple timestamp is aware", r.as_tuple()[0].tzinfo is not None)
check("as_tuple keeps other fields", r.as_tuple()[1] == 1.0)
l = LightningRecord(timestamp=naive, event_type="strike")
check("lightning as_tuple aware", l.as_tuple()[0].tzinfo is not None)
# the actual bug: IST wall clock 01:53 must map to 20:23 UTC when the zone is IST
ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
check("IST 01:53:06 == 20:23:06 UTC", dt.datetime(2026, 11, 13, 1, 53, 6, tzinfo=ist) == utc.replace(second=6))
# spool round trip with an aware and a legacy-naive row
d = tempfile.mkdtemp(); sp = Spool(os.path.join(d, "s.db"))
sp.add(WeatherRecord(timestamp=dt.datetime.now().astimezone().replace(microsecond=0), temp=2.0))
sp.add(WeatherRecord(timestamp=naive, temp=3.0))
rows = sp.pending(10)
check("spool keeps aware offset", rows[0][1].timestamp.tzinfo is not None)
check("legacy naive spool row becomes aware at send time", rows[1][1].as_tuple()[0].tzinfo is not None)
sp.close()
# web tz option validation
sys.path.insert(0, "weather_web")
import db_api
check("tz option added", "TimeZone=Asia/Kolkata" in db_api._session_options({"DB_TIMEZONE": "Asia/Kolkata"}))
check("no tz -> unchanged", db_api._session_options({}) == db_api.SESSION_OPTIONS)
try:
    db_api._session_options({"DB_TIMEZONE": "UTC -c search_path=x"}); bad = False
except ValueError:
    bad = True
check("tz option injection rejected", bad)
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
