import logging
import logging.handlers
import os
import sys

LOG_DIR = os.environ.get('WEATHER_LOG_DIR', '/var/log/weather')
LOG_FILE_NAME = 'weather_daq.log'

logger = logging.getLogger('weather_daq')
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# stderr first: under systemd this reaches journalctl even if the log
# directory is unwritable, so a boot failure is never silent.
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

try:
    os.makedirs(LOG_DIR, exist_ok=True)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(LOG_DIR, LOG_FILE_NAME),
        when="D",          # Rotate daily
        interval=1,
        backupCount=7      # Keep 7 days of logs
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except OSError as e:
    logger.error(f'File logging disabled, {LOG_DIR} is not writable: {e}')
