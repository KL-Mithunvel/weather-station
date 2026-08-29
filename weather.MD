# Operating notes

Deploy from the dev machine:

```
cd spanner
./upload.bat
```

On the Pi:

```
sudo systemctl restart weather_daq
sudo systemctl restart weather_web
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
