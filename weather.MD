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
curl -s localhost:8000/api/weather_web              # current-reading table (HTML)
curl -s localhost:8000/api/weather_summary/<date>    # today's min/max/avg (JSON)
journalctl -u weather_daq -f
tail -f /var/log/weather/weather_daq.log
```

(2026-09-14: `weather_web` was reverted from the status-file-only page back to the
original current-reading + daily min/max/avg table, now querying TimescaleDB directly
via the new `weather_web/db_api.py` - see `.claude/CLAUDE.md`. The old `/healthz` and
`/api/current` status-file endpoints no longer exist; sensor-fault info is folded into
the `/api/weather_web` table's alert banner instead, still read from the DAQ's status
file.)

## Daily reboot

The Pi reboots itself at 03:30 IST (`system/weather_reboot.timer`). `release.bat` installs and
arms it, but only if `weather_daq`, `weather_web` (and nginx, if installed) are enabled at boot -
otherwise the release ends with an error saying the reboot is **not** armed.

```
systemctl list-timers weather_reboot.timer          # next run
sudo /usr/local/sbin/weather-daily-reboot --check   # would it reboot right now? (never reboots)
sudo systemctl start weather_reboot.service         # reboot now, if the checks pass
sudo systemctl disable --now weather_reboot.timer   # turn the daily reboot off
```

After the first night, confirm it worked:

```
last -x reboot shutdown | head            # boot/shutdown history (survives reboots)
cat /var/log/weather/reboot.log           # reboots taken, and reasons for any that were skipped
systemctl is-active weather_daq weather_web nginx
journalctl -u weather_daq -b | head -30   # the DAQ's start-up after this boot
```

Things worth knowing:
- Readings for the ~1-2 minutes the Pi is down are simply not taken. Rain falling in that window
  is lost; the reboot also zeroes the Arduino's rain counter (opening the serial port resets it),
  which is harmless because rainfall is stored as per-reading deltas.
- The hardware watchdog (`system/weather-watchdog.conf`) only takes effect at a boot. Check it with
  `systemctl show -p RuntimeWatchdogUSec` (expect `10s`) and `dmesg | grep -i watchdog`.
- Status file (`/tmp/weather_current.json`) is wiped by a reboot; the web page shows no sensor
  banner until the DAQ's first cycle rewrites it.

## When TimescaleDB is down

Readings keep accumulating in the local spool (`SPOOL_FILE`, default
`/home/klm/weather/data/spool.db`) and upload automatically once the database accepts them.
`spool_pending` on `/api/current` shows the backlog; `timescaledb.last_error` shows why it is
failing. Nothing needs restarting after the database is fixed.

Spool cap is 200,000 readings (~139 days). Past that the oldest are dropped, with an ERROR line
in the log.

## TODO: Grafana setup - blocked on SSH access to the DB host

TimescaleDB lives on a separate host, `timescaledb.apps.smtw.in` (not the Pi - confirmed via
`weather_daq/settings.py` `DB_HOST`), so no data migration is needed for Grafana; it just needs to
be installed on/near that host and pointed at the existing database.

**Blocked as of 2026-09-14**: could not get a diagnostic shell on `timescaledb.apps.smtw.in` to
check what's already running there / plan the Grafana install.
- The Pi's saved `plink` password (klm@rpi4b-weather) does **not** work here - this host only
  accepts SSH public-key auth (`server sent: publickey`).
- Tried Pageant (SSH agent) with no `-pw` - still rejected, so either Pageant has no key loaded, or
  the loaded key isn't authorized on this host's `authorized_keys`.
- Host key fingerprint seen on first connect (accepted/pinned this session, not yet trusted
  long-term): `ssh-ed25519 SHA256:vsUnvj4e8Yz24omARpyC6BfWi6TcGGpFR79WxGVNd3s`

**To unblock**, one of:
1. Point me at a private key file (OpenSSH or `.ppk`) that's authorized on that host, and add a
   `plink -i <path>` permission similar to the existing `rpi4b-weather` one in
   `.claude/settings.local.json`, or
2. Load the right key into Pageant before the next session, or
3. Add my usual working setup's public key to that host's `~/.ssh/authorized_keys` yourself, or
4. Just run the Grafana install/checks yourself and paste output back for review.

Once access works, the plan is: check what's on the host (OS, existing services, disk/ports),
install Grafana, add a Postgres data source pointing at TimescaleDB (`localhost:5432/iiot` if
Grafana runs on the same box), then build panels for temp/rh/wind/rain/lightning. Remember: DB
stores wind direction as the direction the wind blows *toward* (non-standard) - label panels
accordingly, don't invert.

## Public access via Cloudflare Tunnel (hardened 2026-11-12)

The weather page is public-facing, so the Pi itself is never exposed:

```
visitor -> Cloudflare (TLS, DDoS, WAF) -> cloudflared (OUTBOUND tunnel from the Pi)
        -> nginx :80 (rate limits, headers) -> gunicorn 127.0.0.1:8000 -> TimescaleDB (read-only)
```

- **No router port-forward.** Nothing listens to the internet. `ufw` allows 22/80/5353 from the LAN only.
- gunicorn binds `127.0.0.1` and runs in a systemd sandbox; nginx is the only way in.
- The page caches for 30 s and serves the last good copy for 10 min if the DB is down, so visitor
  traffic never turns into DB load. History is limited to the last 31 days; error detail is never shown.
- OS hardening (ufw, fail2ban, sshd, security-only unattended-upgrades at 02:30) is `system/harden.sh`,
  run once with `sudo bash system/harden.sh`. It arms a 5-minute firewall rollback timer; open a NEW ssh
  session to confirm, then `sudo systemctl stop weather-ufw-rollback.timer`.
- `release.bat`/`upload.bat` still use SSH **password** login. Move them to a key, then set
  `PasswordAuthentication no` in `/etc/ssh/sshd_config.d/10-weather-hardening.conf`.

### Creating the tunnel (needs your Cloudflare account - done by hand, the token is a secret)

1. On the Pi: `sudo bash system/install-cloudflared.sh` (installs the program only).
2. Cloudflare dashboard -> Zero Trust -> Networks -> Tunnels -> Create a tunnel (Cloudflared).
   Name it `weather-station`; copy the install token.
3. Add a **Public hostname**: your hostname (e.g. `weather.example.com`) -> Service `HTTP` -> `localhost:80`.
4. On the Pi, run yourself (the token is a credential - keep it out of chat/logs):
   `sudo cloudflared service install <TOKEN>` - it enables the service at boot.
5. Cloudflare -> that domain: SSL/TLS "Full", enable "Always Use HTTPS" and HSTS, and add a WAF
   rate-limiting rule (e.g. 60 requests/min per IP). The Pi's daily reboot restores the tunnel
   automatically because the service is enabled.

### Read-only database role for the web page (needs a DB admin on the TimescaleDB host)

`weather_web/web_settings.py` currently reuses the DAQ's write login. Replace it with:

```sql
CREATE ROLE weather_ro LOGIN PASSWORD '...' CONNECTION LIMIT 10;
GRANT CONNECT ON DATABASE iiot TO weather_ro;
GRANT USAGE ON SCHEMA public TO weather_ro;
GRANT SELECT ON weather TO weather_ro;
ALTER ROLE weather_ro SET statement_timeout = '8s';
ALTER ROLE weather_ro SET default_transaction_read_only = on;
```

While there, the DAQ role is insert-only so `weather_timestamp_key` was never created (re-sent batches
are not deduplicated). As the table owner: `CREATE UNIQUE INDEX IF NOT EXISTS weather_timestamp_key ON weather (timestamp);`

## Timestamps (fixed 2026-11-13)

`weather.timestamp` is `timestamptz` and now always holds the **true instant**. Before the fix the DAQ sent
naive IST wall-clock times and the UTC database session labelled them UTC, so every stored time (403,882 rows,
2025-06-12 onward) was exactly +05:30 too late.

- DAQ: `records.aware()` attaches the Pi's local offset; the acquire loop uses `datetime.now().astimezone()`.
- Web: set `'DB_TIMEZONE': "Asia/Kolkata"` in `web_settings.py` DB_SETTINGS so "today" starts at IST midnight.
  Grafana: leave the dashboard on "Browser" time.
- **Era marker (do not break):** legacy rows have whole-second timestamps and are 5h30m too late; rows written
  since 2026-11-13 always have a NON-ZERO microsecond part (`acquire.reading_timestamp()`, never strip it).
  `(extract(microseconds from timestamp)::bigint % 1000000) = 0` selects exactly the legacy rows. The web
  page's "current reading" prefers new-era rows (`db_api.NEW_ERA`) so legacy rows in the same time range do not win.
- **History correction** (still pending): `system/db/fix_timestamp_offset.sql`, run once by the DB owner. It shifts
  only the legacy rows, so it is safe with the DAQ running and at any time. Until then: history before
  2026-11-13 is 5h30m late, 2026-11-12 20:25 UTC to 2026-11-13 01:55 UTC holds both eras, and the web page
  should keep `DB_TIMEZONE` unset (set `'Asia/Kolkata'` only after the correction).
- `settings.DB_WRITES_ENABLED = False` still pauses uploads (spool keeps filling) if ever needed.
