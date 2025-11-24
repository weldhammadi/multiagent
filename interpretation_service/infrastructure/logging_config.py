import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure un logging simple vers stdout.
    Appelée depuis main.py.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(handler)

