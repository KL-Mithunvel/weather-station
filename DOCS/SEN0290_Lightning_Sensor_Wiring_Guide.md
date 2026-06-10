# DFRobot Gravity Lightning Sensor v1.0 — Raspberry Pi Wiring Guide
**SKU:** SEN0290 | **IC:** AMS AS3935 Franklin Lightning Sensor  
**Full IC datasheet:** `AS3935_Franklin Lightning Sensor IC.pdf` (also in this DOCS folder)

---

## Sensor Overview

| Property | Value |
|---|---|
| Supply voltage | **3.3V – 5.5V** (use 3.3V on Pi — never 5V) |
| Logic level | 0 to VCC |
| Communication | I2C (default address 0x03) |
| Detection range | Up to **40 km** |
| Distance resolution | 14 steps (1 km steps at close range) |
| Dimensions | 30 × 22 mm |
| Connector | 7-pin Gravity I2C |

---

## Sensor Pinout (7-pin Gravity connector)

| Pin # | Label | Type | Description |
|---|---|---|---|
| 1 | VCC | Power | 3.3V supply (from Pi 3.3V rail) |
| 2 | GND | Power | Ground |
| 3 | SCL | I2C | I2C clock signal |
| 4 | SDA | I2C | I2C data signal |
| 5 | ADDR | Config | I2C address selector (DIP switch on board) |
| 6 | IRQ | Interrupt | Lightning alarm — goes HIGH when strike detected |
| 7 | PWR | LED | Power indicator (red LED, no connection needed) |

---

## Raspberry Pi GPIO Wiring

Uses **BCM (Broadcom) numbering** — the number after "GPIO".

```
SEN0290 Sensor          Raspberry Pi Header
──────────────          ──────────────────────────────
  VCC          ──────►  Pin  1  (3.3V)
  GND          ──────►  Pin  6  (GND)
  SCL          ──────►  Pin  5  (GPIO 3 / SCL)
  SDA          ──────►  Pin  3  (GPIO 2 / SDA)
  IRQ          ──────►  Pin 11  (GPIO 17)         ← interrupt, any free GPIO works
  ADDR         ──────   (set by DIP switch, no Pi connection needed)
  PWR          ──────   (LED only, no connection needed)
```

### Pi 40-pin header reference (relevant pins)

```
                3V3 [ 1][ 2] 5V
    SDA — GPIO 2 [ 3][ 4] 5V
    SCL — GPIO 3 [ 5][ 6] GND  ◄── connect GND here
             ...
    IRQ — GPIO17 [11][12] GPIO18
             ...
```

> **IMPORTANT — 3.3V only.** The AS3935 logic is 3.3V. The Gravity connector
> accepts up to 5.5V on VCC but the Pi's I2C lines are 3.3V. Do **not** power
> from the 5V rail — you risk damaging the sensor.

> **SDA pull-up note.** The SEN0290 board is known to omit a pull-up resistor on
> SDA. If you get I2C read errors, add a **10 kΩ resistor between SDA and 3.3V**.
> The Pi's internal weak pull-ups sometimes suffice, but an external resistor is
> more reliable.

---

## I2C Address — DIP Switch Configuration

There is a 2-position DIP switch on the board labelled **A0** and **A1**.

| A0 | A1 | I2C Address | Library constant |
|---|---|---|---|
| ON (1) | ON (1) | **0x03** (default) | `AS3935_ADD3` |
| ON (1) | OFF (0) | 0x01 | `AS3935_ADD1` |
| OFF (0) | ON (1) | 0x02 | `AS3935_ADD2` |

Leave both switches ON (default 0x03) unless you have an address conflict.

---

## Raspberry Pi Software Setup

### 1. Enable I2C
```bash
sudo raspi-config
# → Interfacing Options → I2C → Yes → reboot
```

Verify the sensor is detected (should show `03` at address 0x03):
```bash
sudo apt install i2c-tools
i2cdetect -y 1
```

### 2. Install dependencies and library
```bash
sudo apt-get update
sudo apt-get install python3-dev python3-smbus git

git clone https://github.com/DFRobot/DFRobot_AS3935.git
cd DFRobot_AS3935/python/raspberrypi
```

### 3. Basic usage (I2C mode, IRQ on GPIO 17)
```python
import RPi.GPIO as GPIO
from DFRobot_AS3935_Lib import DFRobot_AS3935

IRQ_PIN   = 17          # BCM pin connected to IRQ
I2C_ADDR  = 0x03        # match DIP switch setting

GPIO.setmode(GPIO.BCM)
GPIO.setup(IRQ_PIN, GPIO.IN)

sensor = DFRobot_AS3935(I2C_ADDR, 1)   # address, I2C bus (1 = /dev/i2c-1)
sensor.reset()
sensor.power_up()

# Configure for outdoor use (reduces false positives from man-made noise)
sensor.set_outdoors()
sensor.set_noise_floor(0)           # 0–7, increase if false triggers
sensor.set_watchdog_threshold(2)    # 1–10
sensor.set_spike_rejection(2)       # 1–11

def lightning_callback(channel):
    interrupt = sensor.get_interrupt_src()
    if interrupt == 0x01:
        print("Noise level too high")
    elif interrupt == 0x04:
        print("Disturber detected (false strike)")
    elif interrupt == 0x08:
        dist = sensor.get_lightning_distKm()
        energy = sensor.get_strike_energy_raw()
        print(f"Lightning! Distance: {dist} km | Energy: {energy}")

GPIO.add_event_detect(IRQ_PIN, GPIO.RISING, callback=lightning_callback)

try:
    input("Listening for lightning... press Enter to quit\n")
finally:
    GPIO.cleanup()
```

---

## Key Sensor Capabilities (AS3935)

| Feature | Detail |
|---|---|
| Detection range | 1 – 40 km |
| Distance estimation | 14 distance steps |
| Noise floor | Adjustable (0–7) — raise if GPIO 17 fires constantly |
| Watchdog threshold | Adjustable (1–10) — raise to reduce false positives |
| Spike rejection | Adjustable (1–11) |
| Indoor/outdoor mode | Outdoor mode reduces man-made noise sensitivity |
| Disturber filtering | Can mask interfering signals (e.g., motors, switching PSUs) |
| Interrupt sources | `0x01` noise, `0x04` disturber, `0x08` lightning |

---

## Checklist Before First Power-On

- [ ] VCC wired to Pi **3.3V** (pin 1), not 5V
- [ ] GND connected
- [ ] SCL → Pi pin 5 (GPIO 3)
- [ ] SDA → Pi pin 3 (GPIO 2)
- [ ] IRQ → Pi pin 11 (GPIO 17) or chosen free GPIO
- [ ] DIP switch matches I2C address in code (default: both ON = 0x03)
- [ ] I2C enabled in `raspi-config`
- [ ] `i2cdetect -y 1` shows `03` (or your chosen address)
- [ ] Optional: 10 kΩ pull-up on SDA if reads are unreliable

---

*Sources: [DFRobot SEN0290 Wiki](https://wiki.dfrobot.com/Gravity:%20Lightning%20Sensor%20SKU:%20SEN0290) · [DFRobot_AS3935 GitHub](https://github.com/DFRobot/DFRobot_AS3935) · AS3935 datasheet (see DOCS folder)*
