import logging.config

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "std": {"format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"}
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "std"}
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}


def setup_logging() -> None:
    logging.config.dictConfig(LOGGING)
