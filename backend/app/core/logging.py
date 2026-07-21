"""
Structured logging configuration for FRIDAY.

Usage:
    from app.core.logging import get_logger

    logger = get_logger(__name__)
    logger.info("Something happened")
"""

import logging
import sys

from app.core.config import settings


def _build_formatter() -> logging.Formatter:
    """Return a human-readable formatter for development and a compact one for production."""
    if settings.is_development:
        fmt = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
        datefmt = "%H:%M:%S"
    else:
        # Compact single-line format suitable for log aggregators.
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
        datefmt = "%Y-%m-%dT%H:%M:%SZ"
    return logging.Formatter(fmt=fmt, datefmt=datefmt)


def configure_logging() -> None:
    """
    Apply the application-wide logging configuration.

    Called once at startup. Subsequent calls are safe (idempotent via ``force=True``).
    """
    logging.basicConfig(
        level=settings.log_level,
        format="%(message)s",   # overridden by handler below
        handlers=[],
        force=True,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_build_formatter())
    handler.setLevel(settings.log_level)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level)

    # Quiet down noisy third-party loggers in production.
    if settings.is_production:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named child of the ``friday`` root logger.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    return logging.getLogger(f"friday.{name}")


# Apply configuration immediately on import so any module that does
# ``from app.core.logging import logger`` gets a properly configured instance.
configure_logging()

# Convenience root logger — used by main.py and other top-level modules.
logger = get_logger("app")
