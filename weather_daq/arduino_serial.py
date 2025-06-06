import serial
import time

class ArduinoSerial:

    def __init__(self, serial_port, baud_rate):
        self.last_rain_value = None
        self.serial = None
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.connect()

    def connect(self):
        # Initialize serial connection
        try:
            self.serial = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            exit(1)
    def close(self):
        self.serial.close()

    def read_values(self):
        try:
            while True:
                if self.serial.in_waiting > 0:
                    line = self.serial.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        values = [ round(float(x),2) for x in line.split(',')]
                        cur_rain_val = values[2] - (self.last_rain_value if self.last_rain_value is not None else values[2])
                        self.last_rain_value = values[2]
                        return {"wind_dir" : values[0], "wind_speed" : values[1], "rain_qty" : cur_rain_val}
        except Exception as e:
            print(f"Error reading serial data: {e}")
            return None

    def reset_arduino(self):
        self.close()
        time.sleep(2)
        self.connect()