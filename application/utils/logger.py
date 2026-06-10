import logging
import os
from logging.handlers import RotatingFileHandler

from application.core.config import settings


def get_logger(service_name: str) -> logging.Logger:
    os.makedirs(settings.LOG_DIR, exist_ok=True)  # Create a Directory with name "/logs" if not present.

    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    log_file = os.path.join(settings.LOG_DIR, f"{service_name}.log")

    handler = RotatingFileHandler(filename=log_file, maxBytes=500 * 1024 * 1024, backupCount=1)  # 500 MB  # only 2 files: .log + .log.1

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s | %(lineno)d | %(funcName)s | %(filename)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


auth_logger = get_logger("auth_service")
