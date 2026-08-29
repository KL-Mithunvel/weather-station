"""Reads `wind_dir,wind_speed,total_rainfall` CSV lines from the Arduino UNO.

Rainfall is cumulative on the Arduino, so read_values() returns the *delta*
since the last read. acquire.py calls reset_arduino() at date rollover to zero
the daily total.

A missing or unplugged Arduino is not fatal: the port is reopened lazily on
each read attempt and failures come back as None.
"""

import time

import serial

from daq_log import logger

# Do not hammer a missing port every cycle.
RECONNECT_INTERVAL = 30


class ArduinoSerial:

    def __init__(self, serial_port, baud_rate):
        self.last_rain_value = None
        self.last_error = None
        self.serial = None
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self._last_connect_attempt = 0.0
        self.connect()

    @property
    def is_open(self):
        return self.serial is not None and self.serial.is_open

    def connect(self):
        """Open the serial port. Returns True on success, never raises."""
        self._last_connect_attempt = time.monotonic()
        try:
            self.serial = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            time.sleep(2)  # Wait for the Arduino to reset after the port opens.
            self.last_error = None
            logger.info(f'Arduino serial open on {self.serial_port}')
            return True
        except (serial.SerialException, OSError) as e:
            self.serial = None
            self.last_error = str(e).strip()
            logger.error(f'Error opening serial port {self.serial_port}: {self.last_error}')
            return False

    def _ensure_open(self):
        if self.is_open:
            return True
        if time.monotonic() - self._last_connect_attempt < RECONNECT_INTERVAL:
            return False
        return self.connect()

    def close(self):
        if self.serial is not None:
            try:
                self.serial.close()
            except (serial.SerialException, OSError):
                pass
            self.serial = None

    def read_values(self):
        if not self._ensure_open():
            return None
        try:
            last_line = None

            # Drain all buffered lines, keep only the most recent.
            while self.serial.in_waiting > 0:
                line = self.serial.readline().decode('utf-8', errors='replace').strip()
                if line:
                    last_line = line

            # If nothing was buffered, block for one fresh line.
            if last_line is None:
                line = self.serial.readline().decode('utf-8', errors='replace').strip()
                if line:
                    last_line = line

            if not last_line:
                self.last_error = 'No data from Arduino'
                return None

            values = [round(float(x), 2) for x in last_line.split(',')]
            if len(values) != 3:
                self.last_error = f'Malformed line: {last_line!r}'
                logger.error(f'Arduino: {self.last_error}')
                return None

            baseline = self.last_rain_value if self.last_rain_value is not None else values[2]
            cur_rain_val = max(0.0, values[2] - baseline)
            self.last_rain_value = values[2]
            self.last_error = None
            return {'wind_dir': values[0], 'wind_speed': values[1], 'rain_qty': cur_rain_val}

        except (serial.SerialException, OSError) as e:
            # Port went away (USB re-enumerated, Arduino reset). Drop it so the
            # next read reopens.
            self.last_error = str(e).strip()
            logger.error(f'Arduino serial error, closing port: {self.last_error}')
            self.close()
            return None
        except ValueError as e:
            self.last_error = f'Unparseable reading: {e}'
            logger.error(f'Arduino: {self.last_error}')
            return None

    def reset_arduino(self):
        """Reopen the port, which resets the board and zeroes its rain counter."""
        self.close()
        time.sleep(2)
        self.connect()
        # Counter is back at 0 after the reset; treat the next reading as the
        # new baseline.
        self.last_rain_value = None
