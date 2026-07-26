import logging
import os
from datetime import datetime

# Global session log filename
SESSION_LOG_FILE = None


def get_logger(name: str) -> logging.Logger:
    global SESSION_LOG_FILE

    # Initialize session log file once
    if SESSION_LOG_FILE is None:
        os.makedirs('logs', exist_ok= True)
        SESSION_LOG_FILE = datetime.now().strftime('logs/session_%Y-%m-%d_%H-%M-%S.log')

    # logging configuration
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers when logger already configured
    if not logger.handlers:
        # writing logs to file
        file_handler = logging.FileHandler(SESSION_LOG_FILE, mode= 'a', encoding= 'utf-8')
        file_handler.setLevel(logging.INFO)

        # terminal output
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)

        # Common formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
            datefmt= '%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger
