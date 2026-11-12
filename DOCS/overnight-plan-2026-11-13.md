# Overnight execution plan - 2026-11-13

Authorised by the user to run unattended ("no need to ask permission when work starts"). Goal: finish every
pending item that does not need something only the user (or the DB owner) can provide, verify tonight's first
real 03:30 reboot, and leave a clear log for review in the morning.

## Ground rules (self-imposed)

- Follow the `prod-vm` protocol for every Pi command: announce, tier, log to `~/.claude/logs/prod-vm/`.
- **No Pi changes between 03:10 and 03:50 IST** (02:30 unattended security upgrades run just before; 03:30 daily reboot).
- Nothing destructive: no `rm` on the Pi, no DB writes (the DB logins are insert-only / read-only by design),
  no credential ever printed or passed on a command line.
- **The page is NOT made public tonight** even if the Cloudflare tunnel could be built: the web process still uses
  the DAQ's write credentials and history is still 5h30m off. Both need the DB owner first.
- Commit + push each finished, tested unit with a clear message. Untracked `.agents/` and `AGENTS.md` stay untouched.

## Work items

| # | Item | Where | Done when |
|---|------|-------|-----------|
| 1 | Fix stray backticks on `DAQ.ino` line 20 (never compiled as committed) | repo + local `arduino-cli` compile | sketch compiles from the repo file unchanged |
| 2 | Web page: show "-" (not `None` / `0`) for missing readings, e.g. while the DHT22 is down | repo + local tests | tests pass, deployed, page checked |
| 3 | Deploy 1+2 to the Pi (before 03:00) | Pi | `deploy.sh` clean, services active |
| 4 | Diagnose the DHT22 fault (read-only first; short test with the DAQ stopped only if needed) | Pi | cause identified or narrowed, written up |
| 5 | Security re-test from outside the Pi: port scan from the PC, headers, rate limit | PC -> Pi | only 22/80 reachable from LAN; results logged |
| 6 | Verify the 02:30 security-update run | Pi, read-only | `unattended-upgrades` log reviewed |
| 7 | **Verify the 03:30 reboot** at ~03:50: uptime reset, ufw/fail2ban/nginx/web/DAQ up, Arduino data flowing, spool empty, DB receiving, watchdog 10 s, no failed units | Pi, read-only | all green, or failure written up with evidence |
| 8 | Retry the Chrome extension; if connected, inspect the Cloudflare dashboard read-only (zones only) | Chrome | outcome recorded; no tunnel/hostname created |
| 9 | Stretch: SHT45 driver scaffold behind `TEMP_SENSOR` setting (default `dht22`, no behaviour change) with fake-I2C tests | repo | tests pass; not deployed as active |
| 10 | Docs: update `weather.MD` open items, `CLAUDE.md`, this file's morning report, memory notes | repo | committed + pushed |

## Blocked on the user / DB owner (not attempted)

| Item | Needs | Default if no answer |
|------|-------|----------------------|
| Cloudflare tunnel | Cloudflare login, hostname, and the user running `cloudflared service install <TOKEN>` | stays uninstalled-service; page stays LAN-only |
| Legacy timestamp correction | DB owner runs `system/db/fix_timestamp_offset.sql` | history stays +5h30m; era marker keeps it separable |
| Read-only DB role + unique index | DB admin (SQL in `weather.MD`) | web keeps DAQ login (risk noted) |
| Disable SSH password login | user moves `release.bat` to a key first (otherwise locks out their own PuTTY/plink) | password login stays ON |
| Pick the replacement sensor | user decision + cable length | scaffold only |

## Morning report

### 03:30 reboot verification (checked 03:50 IST) - all passed
- Reboot ran on schedule (03:30:04), clean shutdown, Pi back up 03:30:16; DAQ booting 03:30:14, Arduino open on /dev/ttyACM0, DB connected.
- ufw active with only the LAN rules, kernel INPUT policy DROP after boot; listeners 22, 80 and 127.0.0.1:8000 only.
- Hardware watchdog active (10 s runtime, 3 min reboot); no failed units; clock synced; 52 C, throttled=0x0.
- Spool pending 0, DB receiving rows; no gap larger than 73 s in the last 3 h, so reboot downtime was under that.
- Page HTTP 200 with security headers; from the PC only ports 22 and 80 are open.
- Known and expected: DHT22 reports fault (worn out, replacement pending); cloudflared inactive (no tunnel yet).

### Needs you or the DB owner
1. Cloudflare tunnel: account/hostname/token, then run `sudo cloudflared service install <TOKEN>` (runbook in weather.MD).
2. DB owner: run `system/db/fix_timestamp_offset.sql`, then set `DB_TIMEZONE` in the Pi's web_settings.py.
3. DB owner: create the read-only `weather_ro` role and the unique index `weather_timestamp_key`.
4. Move release.bat/upload.bat to SSH key auth, then disable SSH password login.
5. Pick the replacement sensor (SHT45 suggested) and bench-test the untested SHT4x driver.

### Files left on the Pi
`/tmp/*` leftovers were cleared by the reboot. `/etc/nginx/sites-available/weather_web.prev` (nginx rollback backup) remains.
