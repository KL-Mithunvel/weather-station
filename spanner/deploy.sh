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

if [ "$units_changed" = 1 ]; then
    echo "Reloading systemd..."
    sudo systemctl daemon-reload
fi

echo "Restarting services..."
sudo systemctl restart weather_daq weather_web
sleep 3

# Non-zero here fails the release: a unit that restarts then dies is not a
# successful deploy.
systemctl is-active weather_daq weather_web

echo
echo "Deployed $(git log -1 --oneline)"
