#!/usr/bin/env bash
# Compile and flash a sketch onto the Arduino UNO attached to rpi4b-weather.
#
# Requires arduino-cli + avrdude + the arduino:avr core installed on the Pi
# (one-time setup, done 2026-09-14) and the dedicated SSH key used by
# pi_ssh.sh.
#
# Usage:
#   spanner/arduino_flash.sh "arduino UNO/test_serial_print/test_serial_print.ino"
#   spanner/arduino_flash.sh "arduino UNO/DAQ.ino"
#
# The argument is a path to a single local .ino file - it's copied into a
# matching-named sketch folder on the Pi (arduino-cli requires the folder and
# file basenames to match), so the local file doesn't need to live in its own
# subfolder.
#
# Stops weather_daq before flashing (it holds /dev/ttyACM0 open) and restarts
# it afterward, whether or not the flash succeeded.
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <local-.ino-file>" >&2
    exit 1
fi

INO_FILE="$1"

if [ ! -f "$INO_FILE" ]; then
    echo "No such file: $INO_FILE" >&2
    exit 1
fi

SKETCH_NAME="$(basename "$INO_FILE" .ino)"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PI_SSH="$SCRIPT_DIR/pi_ssh.sh"
KEY="${HOME}/.ssh/claude_rpi4b_weather"
KNOWN_HOSTS="${HOME}/.ssh/known_hosts_pi"
REMOTE_DIR="arduino_sketches/${SKETCH_NAME}"

echo "== Syncing $INO_FILE -> Pi:~/${REMOTE_DIR}/ =="
"$PI_SSH" "mkdir -p ~/${REMOTE_DIR}"
scp -i "$KEY" -o UserKnownHostsFile="$KNOWN_HOSTS" -o StrictHostKeyChecking=yes \
    "$INO_FILE" "klm@rpi4b-weather:~/${REMOTE_DIR}/${SKETCH_NAME}.ino"

echo "== Stopping weather_daq (releases the serial port) =="
"$PI_SSH" "sudo systemctl stop weather_daq"

cleanup() {
    echo "== Restarting weather_daq =="
    "$PI_SSH" "sudo systemctl start weather_daq"
}
trap cleanup EXIT

echo "== Compiling and uploading to /dev/ttyACM0 =="
"$PI_SSH" "~/bin/arduino-cli compile --fqbn arduino:avr:uno --upload -p /dev/ttyACM0 ~/${REMOTE_DIR}"

echo "== Flash complete =="
