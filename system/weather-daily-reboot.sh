#!/usr/bin/env bash
# Daily reboot for the weather station Pi.
#
# Installed to /usr/local/sbin/weather-daily-reboot by spanner/deploy.sh (root
# owned, so root never runs a file the klm user can edit) and run by
# weather_reboot.service.
#
#   weather-daily-reboot               safety checks, then reboot
#   weather-daily-reboot --check       all the safety checks, never reboots
#   weather-daily-reboot --check-boot  only "is everything enabled at boot?"
#
# Declining to reboot is a normal outcome, not a failure: it is logged and the
# unit still exits 0. --check and --check-boot exit 1 when a reboot would not
# go ahead, so deploy.sh can gate on them.
set -u

MIN_UPTIME="${WEATHER_REBOOT_MIN_UPTIME:-3600}"
UPTIME_FILE="${WEATHER_UPTIME_FILE:-/proc/uptime}"
LOG_FILE="${WEATHER_REBOOT_LOG:-/var/log/weather/reboot.log}"
MODE="${1:-reboot}"

# journald may be volatile on the Pi, so the reboot history also goes to a
# plain file next to the DAQ log.
log() {
    logger -t weather-reboot -- "$*" 2>/dev/null || true
    echo "$*"
    echo "$(date -Is) $*" >> "$LOG_FILE" 2>/dev/null || true
}

uptime_seconds() { cut -d. -f1 "$UPTIME_FILE"; }

# A reboot only brings back what is enabled at boot. A service that was merely
# started by hand would stay down until someone noticed. Prints the reason and
# returns 0 when there is a problem.
boot_problem() {
    local unit
    for unit in weather_daq weather_web; do
        if ! systemctl is-enabled --quiet "$unit"; then
            echo "$unit is not enabled at boot"
            return 0
        fi
    done
    # nginx fronts weather_web but its unit is not ours; only insist on it if
    # it is installed.
    if systemctl cat nginx >/dev/null 2>&1 && ! systemctl is-enabled --quiet nginx; then
        echo "nginx is installed but not enabled at boot"
        return 0
    fi
    return 1
}

# Every reason not to reboot right now. Prints the reason and returns 0 when
# there is one.
reboot_blocker() {
    local up
    up="$(uptime_seconds)"
    # Guards against a reboot loop: if the Pi only just came up (power cut just
    # before the timer fired, a manual reboot), rebooting again gains nothing.
    if [ "$up" -lt "$MIN_UPTIME" ]; then
        echo "up only ${up}s (under ${MIN_UPTIME}s), a reboot now would only repeat a recent outage"
        return 0
    fi
    # Interrupting a package install can leave dpkg half-configured.
    if pgrep -x dpkg >/dev/null || pgrep -x apt-get >/dev/null || pgrep -x apt >/dev/null; then
        echo "a package install/upgrade is running"
        return 0
    fi
    boot_problem
}

case "$MODE" in
    --check-boot)
        if reason="$(boot_problem)"; then
            echo "Not safe to reboot: $reason"
            exit 1
        fi
        echo "Boot readiness OK: weather_daq, weather_web (and nginx if installed) are enabled."
        exit 0
        ;;
    --check)
        if reason="$(reboot_blocker)"; then
            echo "Would skip the reboot: $reason"
            exit 1
        fi
        echo "Would reboot now (up $(uptime_seconds)s)."
        exit 0
        ;;
    reboot)
        ;;
    *)
        echo "usage: $0 [--check | --check-boot]" >&2
        exit 2
        ;;
esac

if reason="$(reboot_blocker)"; then
    log "Skipping daily reboot: $reason"
    exit 0
fi

log "Daily reboot starting (up $(uptime_seconds)s)."
sync
# --no-block: this script runs inside a oneshot unit that the shutdown will
# itself stop, so it must not wait on the reboot job.
exec systemctl --no-block reboot
