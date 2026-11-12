-- One-time correction of weather.timestamp  (run by the DB owner / admin)
-- ============================================================================
-- PROBLEM  Until 2026-11-13 the DAQ sent naive local (IST) times to a
--          timestamptz column. The server session is UTC, so every stored
--          timestamp is the station's wall-clock time labelled as UTC:
--          5 hours 30 minutes AHEAD of the real instant. Verified 2026-11-13:
--          Pi 01:53 IST (20:23 UTC) vs newest row 01:53:06+00; the daily
--          temperature peak sits at 12:00-15:00 "UTC" in every month on record.
--          India has no DST, so the error is exactly +05:30 for ALL rows.
--
-- WHEN     Only while the DAQ is paused (settings.py DB_WRITES_ENABLED = False
--          on the Pi). New, correct rows would otherwise land in the same time
--          range as the wrong ones and could never be told apart. The Pi keeps
--          the readings in its local spool meanwhile and backfills them (with
--          correct timestamps) when writes are re-enabled. Do NOT run twice.
--
-- HOW      psql -h timescaledb.apps.smtw.in -U <owner> -d iiot -v ON_ERROR_STOP=1 -f fix_timestamp_offset.sql
--          UPDATE cannot be used: TimescaleDB chunks have CHECK constraints on
--          the time column, so moving a row to another chunk fails. The rows
--          are shifted into a copy, the table emptied, and the copy re-inserted.
-- ============================================================================

\set ON_ERROR_STOP on
\echo '--- before ---'
SELECT count(*) AS rows, min(timestamp) AS oldest, max(timestamp) AS newest FROM weather;

-- Anything attached to the table that rewriting it could upset? Review the
-- output: continuous aggregates / compression policies need handling first.
SELECT 'continuous aggregate' AS kind, view_name::text AS name FROM timescaledb_information.continuous_aggregates
UNION ALL
SELECT 'compressed chunks', count(*)::text FROM timescaledb_information.chunks
 WHERE hypertable_name = 'weather' AND is_compressed;

BEGIN;

-- Permanent safety copy (drop it after you have checked the result).
CREATE TABLE weather_backup_before_tzfix AS TABLE weather;

CREATE TEMP TABLE weather_shifted ON COMMIT DROP AS
SELECT timestamp - INTERVAL '5 hours 30 minutes' AS timestamp,
       temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty
FROM weather;

TRUNCATE weather;
INSERT INTO weather (timestamp, temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty)
SELECT timestamp, temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty FROM weather_shifted;

-- Guard: row count must be unchanged and nothing may be left in the future.
DO $$
DECLARE before_n bigint; after_n bigint; future_n bigint;
BEGIN
    SELECT count(*) INTO before_n FROM weather_backup_before_tzfix;
    SELECT count(*) INTO after_n  FROM weather;
    SELECT count(*) INTO future_n FROM weather WHERE timestamp > now() + INTERVAL '1 minute';
    IF before_n <> after_n THEN
        RAISE EXCEPTION 'row count changed: % -> %', before_n, after_n;
    END IF;
    IF future_n > 0 THEN
        RAISE EXCEPTION '% rows are still stamped in the future - already corrected, or wrong offset?', future_n;
    END IF;
END $$;

COMMIT;

\echo '--- after (newest should be ~5.5h earlier than before, and not in the future) ---'
SELECT count(*) AS rows, min(timestamp) AS oldest, max(timestamp) AS newest, now() AS db_now FROM weather;

-- ----------------------------------------------------------------------------
-- Optional, recommended afterwards (the DAQ role is insert-only so it could
-- never create this itself; without it ON CONFLICT DO NOTHING cannot dedupe a
-- re-sent batch). If it fails, duplicates exist - inspect them first:
--   SELECT timestamp, count(*) FROM weather GROUP BY 1 HAVING count(*) > 1 LIMIT 20;
-- CREATE UNIQUE INDEX IF NOT EXISTS weather_timestamp_key ON weather (timestamp);
--
-- Once satisfied:   DROP TABLE weather_backup_before_tzfix;
-- ----------------------------------------------------------------------------
