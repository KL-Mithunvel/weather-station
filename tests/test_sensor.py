import os
import sys
import types

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, "weather_daq")
sys.path.insert(0, "weather_web")

# ---- fake hardware stack -------------------------------------------------
state = {"values": [(25.123, 60.456)], "raise": None, "opens": 0, "deinit": 0}


class FakeI2C:
    def deinit(self):
        state["deinit"] += 1


class FakeSHT:
    def __init__(self, i2c, address=0x44):
        state["opens"] += 1
        self.address = address
        self.mode = None

    @property
    def measurements(self):
        if state["raise"]:
            raise OSError(state["raise"])
        v = state["values"][0]
        if len(state["values"]) > 1:
            state["values"].pop(0)
        return v


board = types.ModuleType("board")
board.I2C = lambda: FakeI2C()
board.D4 = "D4"
sht_mod = types.ModuleType("adafruit_sht4x")
sht_mod.SHT4x = FakeSHT
sht_mod.Mode = types.SimpleNamespace(NOHEAT_HIGHPRECISION="noheat")
settings = types.ModuleType("settings")
settings.DB_SETTINGS = {}
settings.DHT_RETRY_COUNT = 3
settings.DHT_PIN = "D4"
settings.TEMP_SENSOR = "sht45"
settings.SHT4X_I2C_ADDR = 0x45
dht_mod = types.ModuleType("dht_sensor")


class FakeDHT:
    status_name_absent = True

    def __init__(self, dht_pin):
        self.pin = dht_pin


dht_mod.DHTSensor = FakeDHT
for name, mod in [("board", board), ("adafruit_sht4x", sht_mod), ("settings", settings), ("dht_sensor", dht_mod)]:
    sys.modules[name] = mod
for n in ("arduino_serial", "pi_cpu_temp"):
    sys.modules[n] = types.ModuleType(n)
sys.modules["arduino_serial"].ArduinoSerial = object
sys.modules["pi_cpu_temp"].PiBoard = object

import time  # noqa: E402
time.sleep = lambda *_: None  # keep retry/recovery waits out of the test run

import sht4x_sensor  # noqa: E402
import acquire  # noqa: E402
from records import WeatherRecord  # noqa: E402

ok = True


def check(n, c):
    global ok
    ok &= bool(c)
    print(("PASS " if c else "FAIL ") + n)


# ---- driver ----------------------------------------------------------------
s = sht4x_sensor.SHT4xSensor(0x45)
check("opens at the configured address", s.sensor.address == 0x45 and not s.is_faulty)
check("high-precision no-heat mode set", s.sensor.mode == "noheat")
check("reading is rounded to 2 dp", s.read_values() == (25.12, 60.46))
state["values"] = [(20.0, 100.8)]
check("RH a hair over 100 is clamped to 100", s.read_values() == (20.0, 100.0))
state["values"] = [(20.0, -2.0)]
check("RH slightly below 0 is clamped to 0", s.read_values() == (20.0, 0.0))
state["values"] = [(200.0, 50.0)]
check("impossible temperature -> (None, None) + fault", s.read_values() == (None, None) and s.is_faulty)
state["values"] = [(20.0, 300.0)]
check("garbage humidity -> (None, None)", s.read_values() == (None, None))
state["values"] = [(21.5, 55.5)]
check("recovers by itself on the next good read", s.read_values() == (21.5, 55.5) and not s.is_faulty and s.last_error is None)
state["raise"] = "I2C bus error"
r = s.read_values()
check("bus error never raises, returns (None, None)", r == (None, None) and s.is_faulty and "I2C bus error" in s.last_error)
state["raise"] = None
opens = state["opens"]
s.recover_sensor()
check("recover_sensor reopens the bus", state["opens"] == opens + 1 and state["deinit"] >= 1 and not s.is_faulty)
check("readings_are_repeating is always False", s.readings_are_repeating() is False)
s.close()
check("close releases the bus and is idempotent", s.sensor is None and (s.close() or True))

# missing library / chip is a fault, never a boot failure
del sys.modules["adafruit_sht4x"]
sys.modules["adafruit_sht4x"] = None  # makes `import adafruit_sht4x` raise ImportError
bad = sht4x_sensor.SHT4xSensor()
check("missing library -> faulty sensor object, no exception", bad.is_faulty and bad.sensor is None and bad.last_error)
check("faulty sensor read returns (None, None)", bad.read_values() == (None, None))
sys.modules["adafruit_sht4x"] = sht_mod

# ---- factory + status key ----------------------------------------------------
settings.TEMP_SENSOR = "sht45"
t = acquire.make_temp_sensor()
check("factory builds the SHT4x when TEMP_SENSOR='sht45'", isinstance(t, sht4x_sensor.SHT4xSensor) and t.i2c_addr == 0x45)
settings.TEMP_SENSOR = "DHT22"
check("factory is case-insensitive and builds the DHT22", isinstance(acquire.make_temp_sensor(), FakeDHT))
del settings.TEMP_SENSOR
check("default (no setting) is the DHT22 - no production change", isinstance(acquire.make_temp_sensor(), FakeDHT))
settings.TEMP_SENSOR = "banana"
check("unknown value falls back to the DHT22", isinstance(acquire.make_temp_sensor(), FakeDHT))

rec = WeatherRecord(temp=21.0, rh=50.0, wind_speed=1.0, wind_dir=90, cpu_temp=45.0)


class Ard:
    last_error = None


class Dht:  # looks like dht_sensor.DHTSensor: no status_name attribute
    is_faulty = False
    last_error = None


h_dht = acquire.assess_health(rec, Dht(), Ard())
check("DHT22 keeps the 'dht22' status key", "dht22" in h_dht and "temp_rh" not in h_dht)
t = acquire.make_temp_sensor if False else None
settings.TEMP_SENSOR = "sht45"
h_sht = acquire.assess_health(rec, acquire.make_temp_sensor(), Ard())
check("SHT4x reports under the 'temp_rh' status key", "temp_rh" in h_sht and h_sht["temp_rh"]["status"] == "ok")

# web banner label for the new key
ws = types.ModuleType("web_settings")
ws.DB_SETTINGS = {}
sys.modules["web_settings"] = ws
import app as A  # noqa: E402
check("web has a public label for 'temp_rh'", A.SENSOR_LABELS.get("temp_rh") == "Temperature / humidity sensor")

print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
