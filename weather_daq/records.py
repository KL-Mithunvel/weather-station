"""Plain data holders shared by the spool and the TimescaleDB writer."""

WEATHER_FIELDS = ('timestamp', 'temp', 'rh', 'cpu_temp', 'wind_speed', 'wind_dir', 'rain_qty')
LIGHTNING_FIELDS = ('timestamp', 'event_type', 'distance_km', 'energy')


class WeatherRecord:
    __slots__ = WEATHER_FIELDS

    def __init__(self, **values):
        for name in WEATHER_FIELDS:
            setattr(self, name, values.get(name))

    def as_tuple(self):
        return tuple(getattr(self, name) for name in WEATHER_FIELDS)

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
        return tuple(getattr(self, name) for name in LIGHTNING_FIELDS)

    def __str__(self):
        body = ', '.join(f'{n}={getattr(self, n)}' for n in LIGHTNING_FIELDS)
        return f'LightningRecord({body})'
