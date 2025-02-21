import logging
import logging.handlers
import os


LOG_DIR = '/var/log/weather'
LOG_FILE_NAME = 'weather_daq.log'
os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, LOG_FILE_NAME)

handler = logging.handlers.TimedRotatingFileHandler(
    log_path,
    when="D",          # Rotate daily
    interval=1,
    backupCount=7      # Keep 7 days of logs1
)

formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)

# Create a logger and attach the handler
logger = logging.getLogger('weather_daq')
logger.setLevel(logging.INFO)
logger.addHandler(handler)
