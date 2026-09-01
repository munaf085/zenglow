"""
Structured logging configuration using structlog.
"""
import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.core.config import settings


def add_app_info(logger: Any, method: str, event_dict: EventDict) -> EventDict:
    """Add application metadata to every log entry."""
    event_dict["service"] = settings.OTEL_SERVICE_NAME
    event_dict["environment"] = settings.ENVIRONMENT
    return event_dict


def setup_logging() -> None:
    """Configure structlog for the application."""
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_app_info,
    ]

    if settings.ENVIRONMENT == "development":
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Silence noisy third-party loggers
    for noisy_logger in ["uvicorn.access", "sqlalchemy.engine"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
