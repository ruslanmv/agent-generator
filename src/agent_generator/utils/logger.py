# ────────────────────────────────────────────────────────────────
#  src/agent_generator/utils/logger.py
# ────────────────────────────────────────────────────────────────
"""
Structured logging configuration using structlog.

Sets up:
* Timestamped JSON output by default.
* Log level from Settings.log_level.
* Automatic enrichment with module and function names.

Usage:
    from agent_generator.utils.logger import get_logger

    log = get_logger(__name__)
    log.info("Starting generation", framework="crewai")
"""

from __future__ import annotations

import logging
import sys

import structlog

from agent_generator.config import get_settings


def _configure_stdlib_logger(level: int) -> None:
    """
    Configure the standard library logger to write to stderr
    with the given level.
    """
    handler = logging.StreamHandler(sys.stderr)
    fmt = logging.Formatter("%(message)s")
    handler.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)


def _structlog_configure() -> None:
    """
    Configure structlog for JSON output with context variables.
    """
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    _configure_stdlib_logger(level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_logger_name,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Configure structlog on import
_structlog_configure()


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Return a structlog logger bound to the given name/module.
    """
    return structlog.get_logger(name)
