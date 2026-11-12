import os
import sys
import types
import datetime as dt

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, "weather_daq")
sys.path.insert(0, "weather_web")
for m in ("board", "settings", "arduino_serial", "dht_sensor", "pi_cpu_temp"):
    sys.modules.setdefault(m, types.ModuleType(m))
sys.modules["settings"].DB_SETTINGS = {}


class _S:
    pass


sys.modules["arduino_serial"].ArduinoSerial = _S
sys.modules["dht_sensor"].DHTSensor = _S
sys.modules["pi_cpu_temp"].PiBoard = _S
import acquire  # noqa: E402

ok = True


def check(n, c):
    global ok
    ok &= bool(c)
    print(("PASS " if c else "FAIL ") + n)


ts = [acquire.reading_timestamp() for _ in range(2000)]
check("2000 stamps: all tz-aware", all(t.tzinfo for t in ts))
check("2000 stamps: none have microsecond == 0", all(t.microsecond != 0 for t in ts))


class FakeDT(dt.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 11, 13, 2, 0, 0, 0)


orig = acquire.datetime
acquire.datetime = FakeDT
t0 = acquire.reading_timestamp()
acquire.datetime = orig
check("exact-zero microsecond is bumped to 1 (second preserved)", t0.microsecond == 1 and t0.second == 0)

import db_api  # noqa: E402

check("NEW_ERA expression is the documented marker", "% 1000000) <> 0" in db_api.NEW_ERA)
sql = open("system/db/fix_timestamp_offset.sql", encoding="utf-8").read()
check("SQL uses the same marker expression", "(extract(microseconds from timestamp)::bigint % 1000000) = 0" in sql)
check("SQL refuses a second run", "weather_backup_before_tzfix already exists" in sql)
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
