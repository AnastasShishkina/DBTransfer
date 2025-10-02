import logging
from src.config import settings

LOG_LEVEL = settings.LOG_LEVEL


import logging.config

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d - %(message)s",
        },
        "access": {
            "format": '%(asctime)s | %(levelname)s | %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },

    "loggers": {
        # твои логи
        "app": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},

        # SQLAlchemy
        "sqlalchemy.engine": {"handlers": ["console"], "level": "WARNING", "propagate": False},

        # Uvicorn
        "uvicorn": {"handlers": ["console"], "level": LOG_LEVEL},
        "uvicorn.error": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "uvicorn.access": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False, "formatter": "access"},
    },

    "root": {"handlers": ["console"], "level": "WARNING"},
}


def setup_logging():
    logging.config.dictConfig(LOGGING)
