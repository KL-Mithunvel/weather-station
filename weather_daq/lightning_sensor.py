import smbus2
import RPi.GPIO as GPIO
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Callable

from daq_log import logger

# AS3935 registers
_REG_AFE_GB      = 0x00
_REG_THRESHOLD   = 0x01
_REG_LIGHTNING   = 0x02
_REG_INT         = 0x03
_REG_ENERGY_LSB  = 0x04
_REG_ENERGY_MSB  = 0x05
_REG_ENERGY_MMSB = 0x06
_REG_DISTANCE    = 0x07
_REG_DIRECT_CMD  = 0x3C

_CMD_RESET       = 0x96
_CMD_CALIB_RCO   = 0x3E

_INT_NOISE       = 0x01
_INT_DISTURBER   = 0x04
_INT_LIGHTNING   = 0x08

_GAIN_OUTDOOR    = 0b01110
_GAIN_INDOOR     = 0b10010

# AS3935 datasheet distance lookup (register bits[5:0] -> km)
_DISTANCE_TABLE = {
    0b000001: 1,   # overhead
    0b000101: 5,
    0b000110: 6,
    0b001000: 8,
    0b001010: 10,
    0b001100: 12,
    0b001110: 14,
    0b010001: 17,
    0b010100: 20,
    0b011000: 24,
    0b011011: 27,
    0b011111: 31,
    0b100010: 34,
    0b101000: 40,
    0b111111: None,  # out of range >40 km
}


@dataclass
class LightningEvent:
    timestamp: datetime
    event_type: str           # 'lightning' | 'noise' | 'disturber'
    distance_km: Optional[int] = None
    energy: Optional[int] = None

    def __str__(self):
        if self.event_type == 'lightning':
            dist = f"{self.distance_km} km" if self.distance_km is not None else ">40 km (out of range)"
            return f"[{self.timestamp}] LIGHTNING  dist={dist}  energy={self.energy}"
        return f"[{self.timestamp}] {self.event_type.upper()}"


class LightningSensor:
    def __init__(self, i2c_addr: int = 0x03, irq_pin: int = 17, i2c_bus: int = 1,
                 outdoor: bool = True, noise_floor: int = 2, watchdog: int = 2,
                 spike_rejection: int = 2, on_event: Optional[Callable] = None):
        self._addr    = i2c_addr
        self._irq_pin = irq_pin
        self._bus     = smbus2.SMBus(i2c_bus)
        self._lock    = threading.Lock()
        self._events: deque = deque()
        self._on_event = on_event

        self._configure(outdoor, noise_floor, watchdog, spike_rejection)
        logger.info(f"LightningSensor ready (I2C=0x{i2c_addr:02X}, IRQ=BCM{irq_pin})")

    # -- low-level I2C --

    def _read(self, reg: int) -> int:
        return self._bus.read_byte_data(self._addr, reg)

    def _write(self, reg: int, val: int):
        self._bus.write_byte_data(self._addr, reg, val)

    def _modify(self, reg: int, mask: int, val: int):
        self._write(reg, (self._read(reg) & ~mask) | (val & mask))

    # -- setup --

    def _configure(self, outdoor: bool, noise_floor: int, watchdog: int, spike_rejection: int):
        self._write(_REG_DIRECT_CMD, _CMD_RESET)
        time.sleep(0.002)

        gain = _GAIN_OUTDOOR if outdoor else _GAIN_INDOOR
        self._modify(_REG_AFE_GB,    0b00111110, gain << 1)
        self._modify(_REG_THRESHOLD, 0b01110000, (noise_floor & 0x07) << 4)
        self._modify(_REG_THRESHOLD, 0b00001111, watchdog & 0x0F)
        self._modify(_REG_LIGHTNING, 0b00001111, spike_rejection & 0x0F)

        self._write(_REG_DIRECT_CMD, _CMD_CALIB_RCO)
        time.sleep(0.002)

    def start(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._irq_pin, GPIO.IN)
        GPIO.add_event_detect(self._irq_pin, GPIO.RISING, callback=self._irq_handler)
        logger.info("LightningSensor IRQ handler active")

    def stop(self):
        try:
            GPIO.remove_event_detect(self._irq_pin)
            GPIO.cleanup(self._irq_pin)
        except Exception:
            pass
        if self._bus:
            self._bus.close()
        logger.info("LightningSensor stopped")

    # -- IRQ handler (runs in GPIO thread) --

    def _irq_handler(self, _channel):
        time.sleep(0.002)  # AS3935 requires ≥2ms before reading interrupt register
        with self._lock:
            try:
                src = self._read(_REG_INT) & 0x0F
                ts  = datetime.now().replace(microsecond=0)

                if src == _INT_LIGHTNING:
                    dist_raw = self._read(_REG_DISTANCE) & 0x3F
                    dist_km  = _DISTANCE_TABLE.get(dist_raw)
                    energy   = (
                        self._read(_REG_ENERGY_LSB) |
                        (self._read(_REG_ENERGY_MSB)  << 8) |
                        ((self._read(_REG_ENERGY_MMSB) & 0x1F) << 16)
                    )
                    event = LightningEvent(ts, 'lightning', dist_km, energy)
                    logger.info(str(event))
                elif src == _INT_DISTURBER:
                    event = LightningEvent(ts, 'disturber')
                    logger.debug(str(event))
                elif src == _INT_NOISE:
                    event = LightningEvent(ts, 'noise')
                    logger.debug(str(event))
                else:
                    return

                self._events.append(event)
                if self._on_event:
                    self._on_event(event)

            except Exception as e:
                logger.error(f"LightningSensor IRQ error: {e}")

    def drain_events(self) -> list:
        """Pop and return all queued events. Call from main acquire loop."""
        events = []
        while self._events:
            try:
                events.append(self._events.popleft())
            except IndexError:
                break
        return events

    # -- tuning helpers --

    def set_noise_floor(self, level: int):
        self._modify(_REG_THRESHOLD, 0b01110000, (max(0, min(7, level)) & 0x07) << 4)

    def set_watchdog(self, level: int):
        self._modify(_REG_THRESHOLD, 0b00001111, max(1, min(10, level)) & 0x0F)

    def set_spike_rejection(self, level: int):
        self._modify(_REG_LIGHTNING, 0b00001111, max(1, min(11, level)) & 0x0F)

    def mask_disturbers(self, enabled: bool):
        self._modify(_REG_INT, 0b00100000, 0b00100000 if enabled else 0)

    def poll(self) -> dict:
        """
        Read current sensor state over I2C without needing an IRQ event.
        Safe to call at any time — use this for continuous monitoring / testing.
        Returns a dict you can print or log.
        """
        with self._lock:
            int_reg   = self._read(_REG_INT) & 0x0F
            dist_raw  = self._read(_REG_DISTANCE) & 0x3F
            afe_gb    = self._read(_REG_AFE_GB)
            threshold = self._read(_REG_THRESHOLD)

        event_map = {
            _INT_LIGHTNING:  'lightning',
            _INT_DISTURBER:  'disturber',
            _INT_NOISE:      'noise',
        }
        last_event   = event_map.get(int_reg, 'none')
        last_dist_km = _DISTANCE_TABLE.get(dist_raw)   # None = out of range, 0 = no data yet

        noise_floor = (threshold >> 4) & 0x07
        gain_bits   = (afe_gb >> 1) & 0x1F
        gain_name   = {_GAIN_OUTDOOR: 'outdoor', _GAIN_INDOOR: 'indoor'}.get(gain_bits, f'0b{gain_bits:05b}')

        return {
            'last_event':    last_event,
            'last_dist_km':  last_dist_km,
            'dist_raw':      dist_raw,
            'noise_floor':   noise_floor,
            'gain':          gain_name,
        }

    def read_config(self) -> dict:
        """Read back AS3935 config registers — use this to confirm I2C is working without needing a storm."""
        afe_gb    = self._read(_REG_AFE_GB)
        threshold = self._read(_REG_THRESHOLD)
        lightning = self._read(_REG_LIGHTNING)

        gain_bits       = (afe_gb >> 1) & 0x1F
        noise_floor     = (threshold >> 4) & 0x07
        watchdog        = threshold & 0x0F
        spike_rejection = lightning & 0x0F
        min_strikes     = (lightning >> 4) & 0x03

        gain_name = {_GAIN_OUTDOOR: 'OUTDOOR', _GAIN_INDOOR: 'INDOOR'}.get(gain_bits, f'UNKNOWN (0b{gain_bits:05b})')

        return {
            'raw_afe_gb':    f'0x{afe_gb:02X}',
            'raw_threshold': f'0x{threshold:02X}',
            'raw_lightning': f'0x{lightning:02X}',
            'gain':          gain_name,
            'noise_floor':   noise_floor,
            'watchdog':      watchdog,
            'spike_rejection': spike_rejection,
            'min_strikes_before_irq': [1, 5, 9, 16][min_strikes],
        }


# ---------------------------------------------------------------------------
# Run directly for live terminal monitor: python lightning_sensor.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    import settings

    POLL_INTERVAL = 5  # seconds between register reads

    print("=" * 60)
    print("  DFRobot SEN0290 / AS3935 — Sensor Test")
    print(f"  I2C bus  : {settings.LIGHTNING_I2C_BUS}  (/dev/i2c-{settings.LIGHTNING_I2C_BUS})")
    print(f"  I2C addr : 0x{settings.LIGHTNING_I2C_ADDR:02X}")
    print(f"  IRQ pin  : BCM {settings.LIGHTNING_IRQ_PIN}")
    print("=" * 60)

    # ── Step 1: Init — the I2C write in _configure() proves the bus is alive ──
    print("\n[1/3] Initialising sensor over I2C...")
    try:
        sensor = LightningSensor(
            i2c_addr        = settings.LIGHTNING_I2C_ADDR,
            irq_pin         = settings.LIGHTNING_IRQ_PIN,
            i2c_bus         = settings.LIGHTNING_I2C_BUS,
            outdoor         = True,
            noise_floor     = 2,
            watchdog        = 2,
            spike_rejection = 2,
        )
    except Exception as e:
        print(f"\n  FAIL — I2C error: {e}")
        print("  Check: SDA→GPIO2, SCL→GPIO3, VCC=3.3V, GND,")
        print("         I2C enabled (sudo raspi-config → Interface Options),")
        print("         DIP switches: both ON=0x03, S1 OFF=0x02, S2 OFF=0x01")
        sys.exit(1)

    # ── Step 2: Read back config registers ──
    print("  OK — sensor responded\n")
    print("[2/3] Config register readback:")
    cfg = sensor.read_config()
    print(f"  Gain               : {cfg['gain']}")
    print(f"  Noise floor        : {cfg['noise_floor']}  (0=sensitive … 7=deaf)")
    print(f"  Watchdog           : {cfg['watchdog']}")
    print(f"  Spike rejection    : {cfg['spike_rejection']}")
    print(f"  Min strikes/IRQ    : {cfg['min_strikes_before_irq']}")
    print(f"  Raw 0x00/0x01/0x02 : {cfg['raw_afe_gb']}  {cfg['raw_threshold']}  {cfg['raw_lightning']}")
    print("\n  I2C confirmed — sensor is alive.\n")

    # ── Step 3: Polling + IRQ event listener ──
    # poll() reads registers over I2C every POLL_INTERVAL seconds — no storm needed.
    # IRQ callback fires instantly when a real event occurs.
    print("[3/3] Running — polling every 5s AND listening for IRQ events.")
    print("      Trigger test: hold a phone charger near the antenna → disturber")
    print("      Ctrl+C to stop.\n")

    def on_event(event: LightningEvent):
        if event.event_type == 'lightning':
            dist = f"{event.distance_km} km" if event.distance_km is not None else ">40 km"
            print(f"\n  *** LIGHTNING  {event.timestamp}  dist={dist}  energy={event.energy}")
        elif event.event_type == 'disturber':
            print(f"  [IRQ] disturber  {event.timestamp}  (man-made EMF)")
        elif event.event_type == 'noise':
            print(f"  [IRQ] noise      {event.timestamp}  (raise noise_floor if frequent)")

    sensor._on_event = on_event
    sensor.start()

    try:
        while True:
            s = sensor.poll()
            dist_str = (
                'overhead' if s['last_dist_km'] == 1
                else f"{s['last_dist_km']} km" if s['last_dist_km'] is not None
                else 'no data'
            )
            print(
                f"  poll  last_event={s['last_event']:<10}  "
                f"last_dist={dist_str:<12}  "
                f"noise_floor={s['noise_floor']}  gain={s['gain']}"
            )
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        sensor.stop()
        GPIO.cleanup()
