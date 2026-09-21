#!/usr/bin/env bash
# Release deploy. Runs ON the Pi, invoked by spanner/release.bat.
#
# Pulls the pushed commit, installs requirements and systemd units only if they
# actually changed, restarts both services and verifies they came back up.
set -euo pipefail

REPO="${WEATHER_HOME:-$HOME/weather}"
BRANCH="${1:-main}"
UNIT_DIR="${UNIT_DIR:-/etc/systemd/system}"
FORCE="${2:-}"

cd "$REPO"

if [ ! -d .git ]; then
    echo "ERROR: $REPO is not a git repository."
    echo "See the one-time setup in weather.MD."
    exit 1
fi

# upload.bat (the dev shortcut) pscp's files straight into this tree, which
# leaves it dirty and blocks a fast-forward pull. That is the expected state
# after dev testing, but discarding work is never silent.
dirty="$(git status --porcelain --untracked-files=no)"
if [ -n "$dirty" ]; then
    echo "Tracked files have uncommitted changes on the Pi:"
    echo "$dirty"
    if [ "$FORCE" != "--force" ]; then
        echo
        echo "These are usually leftovers from upload.bat. If they are, re-run"
        echo "the release with --force to discard them. If not, copy them off"
        echo "the Pi first - --force runs 'git reset --hard'."
        exit 1
    fi
    echo "Discarding local changes (--force)..."
    git reset --hard
fi

before="$(git rev-parse HEAD)"
git fetch origin "$BRANCH"
git merge --ff-only "origin/$BRANCH"
after="$(git rev-parse HEAD)"

if [ "$before" = "$after" ]; then
    echo "Already up to date at $(git log -1 --oneline)"
else
    echo "Pulled $(git rev-list --count "$before..$after") commit(s):"
    git log --oneline "$before..$after"
fi

changed="$(git diff --name-only "$before" "$after")"
changed_file() { echo "$changed" | grep -qx "$1"; }

if changed_file weather_daq/requirements.txt; then
    echo "weather_daq requirements changed, installing..."
    weather_daq/.venv-daq/bin/pip install -q -r weather_daq/requirements.txt
fi
if changed_file weather_web/requirements.txt; then
    echo "weather_web requirements changed, installing..."
    weather_web/.venv-web/bin/pip install -q -r weather_web/requirements.txt
fi

# systemd reads /etc/systemd/system, not the repo, so unit edits are inert
# until copied. cmp avoids touching /etc on every release.
units_changed=0
install_unit() {
    local src="$1"
    local name
    name="$(basename "$src")"
    if ! cmp -s "$src" "$UNIT_DIR/$name"; then
        echo "Installing $name..."
        sudo cp "$src" "$UNIT_DIR/$name"
        units_changed=1
    fi
}
install_unit weather_daq/weather_daq.service
install_unit weather_web/install/weather_web.service
install_unit system/weather_reboot.service
install_unit system/weather_reboot.timer

if [ "$units_changed" = 1 ]; then
    echo "Reloading systemd..."
    sudo systemctl daemon-reload
fi

# Root-owned copy of the reboot script, so root never executes a file the klm
# user can edit.
REBOOT_BIN="${REBOOT_BIN:-/usr/local/sbin/weather-daily-reboot}"
if ! cmp -s system/weather-daily-reboot.sh "$REBOOT_BIN"; then
    echo "Installing $REBOOT_BIN..."
    sudo install -D -m 755 -o root -g root system/weather-daily-reboot.sh "$REBOOT_BIN"
fi

# Hardware watchdog. PID 1 reads this at boot, so a change is picked up by the
# next reboot rather than applied to the running system.
WATCHDOG_CONF="${WATCHDOG_CONF:-/etc/systemd/system.conf.d/weather-watchdog.conf}"
if ! cmp -s system/weather-watchdog.conf "$WATCHDOG_CONF"; then
    echo "Installing $WATCHDOG_CONF (takes effect at next boot)..."
    sudo install -D -m 644 -o root -g root system/weather-watchdog.conf "$WATCHDOG_CONF"
fi

echo "Restarting services..."
sudo systemctl restart weather_daq weather_web
sleep 3

# Non-zero here fails the release: a unit that restarts then dies is not a
# successful deploy.
systemctl is-active weather_daq weather_web

# Daily reboot. A reboot only restores what is enabled at boot, so make sure
# our units are, and refuse to arm the timer if anything else the station needs
# (nginx) is not - the first unattended reboot would otherwise take it down.
echo
echo "Arming the daily reboot..."
sudo systemctl enable weather_daq weather_web
if ! "$REBOOT_BIN" --check-boot; then
    sudo systemctl disable --now weather_reboot.timer 2>/dev/null || true
    echo
    echo "The code is deployed and running, but the daily reboot is NOT armed."
    echo "Fix the above (e.g. 'sudo systemctl enable nginx'), then re-run the release."
    exit 1
fi
sudo systemctl enable weather_reboot.timer
# Restart rather than start, so an edited OnCalendar takes effect.
sudo systemctl restart weather_reboot.timer
# A calendar spec systemd cannot parse leaves the timer inactive; fail loudly.
systemctl is-active weather_reboot.timer
systemctl list-timers weather_reboot.timer --no-pager

echo
echo "Deployed $(git log -1 --oneline)"
