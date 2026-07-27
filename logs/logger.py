import logging
import os
from datetime import datetime
from typing import Literal


SESSION_LOG_FILE = None
LOGGING_ENABLED = True
LOGGING_HANDLERS: Literal['file', 'stream', 'both'] = 'both'
LOGGING_LEVEL: logging._Level = logging.INFO
LOGGING_DIR: str = 'logs'


def configure(
    *,
    enabled: bool = True,
    handlers: Literal['file', 'stream', 'both'] = 'both',
    level: logging._Level = logging.INFO,
    directory: str = 'logs'
):
    global LOGGING_ENABLED, LOGGING_HANDLERS, LOGGING_LEVEL, LOGGING_DIR

    LOGGING_ENABLED = enabled
    LOGGING_HANDLERS = handlers
    LOGGING_LEVEL = level
    LOGGING_DIR = directory


def get_logger(name: str) -> logging.Logger:
    global SESSION_LOG_FILE

    if SESSION_LOG_FILE is None:
        os.makedirs('logs', exist_ok= True)
        SESSION_LOG_FILE = datetime.now().strftime(
            'logs/session_%Y-%m-%d_%H-%M-%S.log'
        )

    logger = logging.getLogger(name)

    logger.setLevel(logging.INFO)

    # Remove previous handlers
    logger.handlers.clear()

    # Disable logging
    if not LOGGING_ENABLED:
        logger.disabled = True
        return logger

    logger.disabled = False

    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    if LOGGING_HANDLERS in ('file', 'both'):
        fh = logging.FileHandler(
            SESSION_LOG_FILE,
            encoding='utf-8'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    if LOGGING_HANDLERS in ('stream', 'both'):
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    return logger