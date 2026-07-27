import logging
from pathlib import Path
from datetime import datetime

# Create logs directory
LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok= True)

# Session log file
SESSION_LOG = LOG_DIR / datetime.now().strftime(
    'session_%Y-%m-%d_%H-%M-%S.log'
)

# Create logger
logger = logging.getLogger('orion')
logger.setLevel(logging.INFO)
logger.propagate = False

# Prevent duplicate handlers if module is reloaded
if not logger.handlers:
    file_handler = logging.FileHandler(
        SESSION_LOG,
        encoding= 'utf-8'
    )

    file_handler.setFormatter(
        logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
    )

    logger.addHandler(file_handler)
