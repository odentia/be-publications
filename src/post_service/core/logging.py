import logging
import sys
from typing import Any

# TODO: Использовать common-logging
# from common_logging import init_logging, get_logger

from rich.console import Console
from rich.logging import RichHandler


def init_logging(level: str = "INFO") -> None:
    """Initialize logging with Rich handler"""
    # TODO: Заменить на common-logging
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=Console(stderr=True), rich_tracebacks=True)],
    )


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)