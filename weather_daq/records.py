"""Plain data holders shared by the spool and the TimescaleDB writer."""

WEATHER_FIELDS = ('timestamp', 'temp', 'rh', 'cpu_temp', 'wind_speed', 'wind_dir', 'rain_qty')
LIGHTNING_FIELDS = ('timestamp', 'event_type', 'distance_km', 'energy')


def aware(ts):
    """Return `ts` as a timezone-aware datetime.

    A naive datetime is the Pi's local wall-clock time (that is what
    datetime.now() returns). Sent to a timestamptz column as-is, PostgreSQL
    reads it in the *session* time zone - UTC on our server - and stores a
    time that is 5h30m ahead of reality. Attaching the local offset here makes
    the stored value the true instant regardless of the session time zone.
    """
    if ts is not None and ts.tzinfo is None:
        return ts.astimezone()
    return ts


class WeatherRecord:
    __slots__ = WEATHER_FIELDS

    def __init__(self, **values):
        for name in WEATHER_FIELDS:
            setattr(self, name, values.get(name))

    def as_tuple(self):
        values = tuple(getattr(self, name) for name in WEATHER_FIELDS)
        return (aware(values[0]),) + values[1:]

    def as_dict(self):
        return {name: getattr(self, name) for name in WEATHER_FIELDS}

    def __str__(self):
        body = ', '.join(f'{n}={getattr(self, n)}' for n in WEATHER_FIELDS)
        return f'WeatherRecord({body})'


class LightningRecord:
    __slots__ = LIGHTNING_FIELDS

    def __init__(self, **values):
        for name in LIGHTNING_FIELDS:
            setattr(self, name, values.get(name))

    def as_tuple(self):
        values = tuple(getattr(self, name) for name in LIGHTNING_FIELDS)
        return (aware(values[0]),) + values[1:]

    def __str__(self):
        body = ', '.join(f'{n}={getattr(self, n)}' for n in LIGHTNING_FIELDS)
        return f'LightningRecord({body})'
