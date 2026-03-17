"""Logging configuration."""
import logging
import logging.config
from utils.config import settings


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "default": {
            "level": settings.log_level,
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["default"],
            "level": settings.log_level,
            "propagate": True,
        }
    },
}


def setup_logging():
    """Configure logging from LOGGING_CONFIG."""
    logging.config.dictConfig(LOGGING_CONFIG)
    return logging.getLogger(__name__)
