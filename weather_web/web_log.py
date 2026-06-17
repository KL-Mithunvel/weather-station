import logging
import logging.handlers
import os

_PI_LOG_DIR = '/var/log/weather'
_LOCAL_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
LOG_FILE_NAME = 'weather_web.log'

LOG_DIR = _LOCAL_LOG_DIR if os.environ.get('WEATHER_ENV') == 'dev' else _PI_LOG_DIR
os.makedirs(LOG_DIR, exist_ok=True)

log_path = os.path.join(LOG_DIR, LOG_FILE_NAME)

handler = logging.handlers.TimedRotatingFileHandler(
    log_path,
    when="D",          # Rotate daily
    interval=1,
    backupCount=7       # Keep 7 days of logs
)

formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)

logger = logging.getLogger('weather_web')
logger.setLevel(logging.INFO)
logger.addHandler(handler)
