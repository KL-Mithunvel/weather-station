-- One-time correction of LEGACY weather.timestamp rows  (run by the DB owner / admin)
-- ============================================================================
-- PROBLEM  Until 2026-11-13 the DAQ sent naive local (IST) times to a
--          timestamptz column. The server session is UTC, so every legacy
--          timestamp is the station's wall-clock time labelled as UTC:
--          5 hours 30 minutes AHEAD of the real instant. Verified 2026-11-13:
--          Pi 01:53 IST (20:23 UTC) vs newest row 01:53:06+00; the daily
--          temperature peak sits at 12:00-15:00 "UTC" in every month on record.
--          India has no DST, so the error is exactly +05:30 for every legacy row.
--
-- ERA MARKER  Legacy rows have WHOLE-SECOND timestamps. Rows written by the
--          fixed DAQ (from 2026-11-13) carry a NON-ZERO microsecond part and
--          are already correct. So the legacy rows are exactly:
--              (extract(microseconds from timestamp)::bigint % 1000000) = 0
--          This script shifts ONLY those, so it is safe to run while the DAQ
--          is running, at any time after the fix. Run it ONCE: the shifted rows
--          are still whole-second, so a second run would shift them again. The
--          script refuses a second run (it checks for its own backup table).
--
-- HOW      psql -h timescaledb.apps.smtw.in -U <owner> -d iiot -v ON_ERROR_STOP=1 -f fix_timestamp_offset.sql
--          UPDATE cannot be used: TimescaleDB chunks have CHECK constraints on
--          the time column, so moving a row to another chunk fails. The legacy
--          rows are deleted and re-inserted with the shifted time.
-- ============================================================================

\set ON_ERROR_STOP on

\echo '--- before ---'
SELECT count(*) FILTER (WHERE (extract(microseconds from timestamp)::bigint % 1000000) = 0) AS legacy_rows,
       count(*) FILTER (WHERE (extract(microseconds from timestamp)::bigint % 1000000) <> 0) AS fixed_era_rows,
       max(timestamp) FILTER (WHERE (extract(microseconds from timestamp)::bigint % 1000000) = 0) AS newest_legacy,
       now() AS db_now
FROM weather;

-- Anything attached to the table that rewriting rows could upset? Review the
-- output: continuous aggregates / compressed chunks need handling first.
SELECT 'continuous aggregate' AS kind, view_name::text AS name FROM timescaledb_information.continuous_aggregates
UNION ALL
SELECT 'compressed chunks', count(*)::text FROM timescaledb_information.chunks
 WHERE hypertable_name = 'weather' AND is_compressed;

BEGIN;

-- Refuse a second run.
DO $$ BEGIN
    IF to_regclass('public.weather_backup_before_tzfix') IS NOT NULL THEN
        RAISE EXCEPTION 'weather_backup_before_tzfix already exists - this script has been run before';
    END IF;
END $$;

-- Permanent safety copy of the legacy rows (drop it once you have checked the result).
CREATE TABLE weather_backup_before_tzfix AS
SELECT * FROM weather WHERE (extract(microseconds from timestamp)::bigint % 1000000) = 0;

DELETE FROM weather WHERE (extract(microseconds from timestamp)::bigint % 1000000) = 0;

INSERT INTO weather (timestamp, temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty)
SELECT timestamp - INTERVAL '5 hours 30 minutes', temp, rh, cpu_temp, wind_speed, wind_dir, rain_qty
FROM weather_backup_before_tzfix;

-- Guards: something was shifted, nothing left in the future.
DO $$
DECLARE legacy_n bigint; total_n bigint; future_n bigint;
BEGIN
    SELECT count(*) INTO legacy_n FROM weather_backup_before_tzfix;
    SELECT count(*) INTO total_n  FROM weather;
    SELECT count(*) INTO future_n FROM weather WHERE timestamp > now() + INTERVAL '1 minute';
    IF legacy_n = 0 THEN
        RAISE EXCEPTION 'no legacy rows found - already corrected?';
    END IF;
    IF future_n > 0 THEN
        RAISE EXCEPTION '% rows are still stamped in the future - wrong offset?', future_n;
    END IF;
    RAISE NOTICE 'shifted % legacy rows; table now holds % rows', legacy_n, total_n;
END $$;

COMMIT;

\echo '--- after ---'
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
