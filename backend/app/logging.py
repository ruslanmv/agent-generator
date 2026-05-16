"""Structured logging via structlog.

Emits JSON in production and a colorized console renderer in dev so
the same log line is grep-able both ways. Configured once at startup
from ``configure_logging()``; subsequent ``structlog.get_logger()``
calls inherit the processors.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def configure_logging(level: str = "INFO", *, json: bool = False) -> None:
    """Initialise stdlib logging + structlog.

    Args:
        level: stdlib log level name.
        json: when True, emit JSON (prod); else colorized console (dev).
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    processors.append(
        structlog.processors.JSONRenderer()
        if json
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(level)
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
