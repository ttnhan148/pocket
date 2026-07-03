"""Structured Logging Configuration."""

from __future__ import annotations

import logging
import sys

from app.config import Settings


def setup_logging(settings: Settings | None = None) -> None:
    """Configure structured logging for the application."""
    if settings is None:
        settings = Settings()

    log_level = logging.getLevelName(settings.log_level.upper())
    if not isinstance(log_level, int):
        log_level = logging.INFO

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clean existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Standard out stream handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Development vs Production logging format
    if settings.env == "development":
        # Colorful human-readable logs
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # Standard structured/production logging
        formatter = logging.Formatter(
            fmt='{"timestamp":"%(asctime)s", "level":"%(levelname)s", "logger":"%(name)s", "message":"%(message)s"}',
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure third-party loggers to be less verbose
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.env == "development" else logging.WARNING
    )
