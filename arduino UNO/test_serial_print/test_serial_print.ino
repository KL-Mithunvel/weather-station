// Minimal hardware sanity check, independent of the weather meter kit
// wiring/library - confirms the Uno itself, the USB-serial link, and the
// flashing tooling all work. Flash this with spanner/arduino_flash.sh when
// the DAQ sketch's serial line goes silent, to isolate board/link problems
// from sensor wiring problems.
void setup() {
    Serial.begin(115200);
    pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
    digitalWrite(LED_BUILTIN, HIGH);
    Serial.println("test_serial_print alive");
    delay(500);
    digitalWrite(LED_BUILTIN, LOW);
    delay(500);
}
