# Operating notes

## Deploying

Two paths, from `spanner/`:

```
release.bat          commit -> push -> Pi pulls -> restart      (the real one)
release.bat --force  same, but discards leftover upload.bat files on the Pi
upload.bat           pscp the working tree -> restart           (dev shortcut)
```

`release.bat` refuses to run with uncommitted changes, since they would not be
in the pushed commit. It installs requirements and systemd units only when
those files actually changed, then verifies both units came back up.

`upload.bat` skips git entirely so uncommitted work can be tested on real
hardware. It does **not** install systemd units or requirements, and it leaves
the Pi's git tree dirty - the next `release.bat` will say so and want `--force`.

Neither script deletes anything on the Pi. After removing a file from the repo,
delete it there by hand.

### One-time: make `~/weather` a git checkout

The Pi was originally deployed by pscp, so `~/weather` is a plain directory.
`release.bat` needs it to be a checkout. This keeps `settings.py`, the venvs and
`data/` in place, since none of them are tracked:

```
cd ~/weather
git init
git remote add origin https://github.com/KL-Mithunvel/weather-station.git
git fetch origin main
git checkout -f -t origin/main
git status          # settings.py and the venvs should show as ignored, not deleted
```

## Restarting by hand

```
sudo systemctl restart weather_daq weather_web
systemctl is-active weather_daq weather_web
```

Check it is alive:

```
curl -s localhost:8000/healthz          # 200 = fresh reading, 503 = stale/stopped
curl -s localhost:8000/api/current      # latest reading + sensor health + spool depth
journalctl -u weather_daq -f
tail -f /var/log/weather/weather_daq.log
```

## When TimescaleDB is down

Readings keep accumulating in the local spool (`SPOOL_FILE`, default
`/home/klm/weather/data/spool.db`) and upload automatically once the database accepts them.
`spool_pending` on `/api/current` shows the backlog; `timescaledb.last_error` shows why it is
failing. Nothing needs restarting after the database is fixed.

Spool cap is 200,000 readings (~139 days). Past that the oldest are dropped, with an ERROR line
in the log.
