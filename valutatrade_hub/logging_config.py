# valutatrade_hub/logging_config.py
import logging
import os
from logging.handlers import RotatingFileHandler

from .infra.settings import settings


def setup_logging():
    """Настраивает глобальный логгер для приложения."""
    log_path = settings.get("log_path", "logs")
    log_file = settings.get("log_file", "actions.log")
    log_format = settings.get("log_format", "%(asctime)s - %(levelname)s - %(message)s")

    os.makedirs(log_path, exist_ok=True)

    log_file_path = os.path.join(log_path, log_file)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=1024 * 1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(log_format))

    if not logger.handlers:
        logger.addHandler(file_handler)
