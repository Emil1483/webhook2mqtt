import logging
from logging.config import dictConfig


def setup_logging(level=logging.DEBUG):
    default_format = "[%(levelname)s|%(filename)s|L%(lineno)s] %(asctime)s: %(message)s"

    config = {
        "version": 1,
        "disable_existing_loggers": True,  # If we want 3rd party libraries to log to stdout too
        "filters": {},
        "formatters": {
            "colored": {
                "()": "colorlog.ColoredFormatter",
                "format": f"%(log_color)s{default_format}",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
                "force_color": True,
                "log_colors": {
                    "DEBUG": "light_black",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "FATAL": "bold_red",
                    "CRITICAL": "bold_red",
                },
            },
            "default": {
                "format": default_format,
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
        },
        "handlers": {
            "stdout": {
                "class": "colorlog.StreamHandler",
                "formatter": "colored",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "root": {
                "level": level,
                "handlers": ["stdout"],
            },
        },
    }

    dictConfig(config)
