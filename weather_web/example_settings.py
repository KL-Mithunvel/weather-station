"""Template for the gitignored weather_web/web_settings.py. Copy and fill in.

weather_web now reads TimescaleDB directly (read-only) to build the current-
reading table and daily summaries, so it needs the same Postgres connection
details as weather_daq/settings.py - use the same TimescaleDB credentials,
just without write access if you want to create a read-only DB role for it.
"""

DB_SETTINGS = {
    'DB_HOST': "",
    'DB_PORT': "5432",
    'DB_USER': "",
    'DB_PASSWORD': "",
    'DB_NAME': "",
    # Session time zone: decides where "today" starts and how times are shown.
    # Stored timestamps are true instants, so set this to the station's zone.
    'DB_TIMEZONE': "Asia/Kolkata",
}
