#!/usr/bin/env bash
# Non-interactive SSH helper for the weather station Pi (rpi4b-weather), using a
# dedicated automation key so no password ever needs to be typed or piped in.
#
# One-time setup (already done on this machine):
#   ssh-keygen -t ed25519 -f ~/.ssh/claude_rpi4b_weather -N "" -C "claude-code-automation"
#   # then append ~/.ssh/claude_rpi4b_weather.pub to ~/.ssh/authorized_keys on the Pi
#
# Usage:
#   spanner/pi_ssh.sh 'systemctl status weather_web nginx weather_daq --no-pager'
#   spanner/pi_ssh.sh 'sudo tail -n 50 /var/log/nginx/error.log'
#
# Read-only diagnostics need no extra flags. Anything that changes state on the
# Pi (config edits, service restarts, package upgrades, reboot) should only be
# run with the same care as any other production change to this host.
set -euo pipefail

KEY="${HOME}/.ssh/claude_rpi4b_weather"
KNOWN_HOSTS="${HOME}/.ssh/known_hosts_pi"
HOST="klm@rpi4b-weather"

if [ ! -f "$KEY" ]; then
    echo "Missing automation key at $KEY - see setup instructions in this script's header." >&2
    exit 1
fi

exec ssh -i "$KEY" \
    -o BatchMode=yes \
    -o UserKnownHostsFile="$KNOWN_HOSTS" \
    -o StrictHostKeyChecking=yes \
    "$HOST" "$@"
