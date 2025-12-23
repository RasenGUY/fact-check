import sys
from typing import Any, List, Optional
from logging import basicConfig, DEBUG, getLogger
from structlog import (
    get_logger as get_structlog_logger,
    configure,
    processors,
    stdlib,
    contextvars,
    dev,
    make_filtering_bound_logger,
)
from app.constants.app import APP_NAME


def clear_api_logging():
    """Clear uvicorn default loggers to prevent duplicate logs."""
    getLogger("uvicorn").handlers.clear()
    getLogger("uvicorn").propagate = False
    getLogger("uvicorn.access").handlers.clear()
    getLogger("uvicorn.access").propagate = False


def setup_processors(shared_processors: List):
    """Configure structlog processors based on environment."""
    if sys.stdout.isatty():  # dev
        configure(
            processors=shared_processors + [dev.ConsoleRenderer()]
        )
    else:  # prod (typically in docker)
        configure(
            processors=shared_processors + [processors.JSONRenderer()]
        )


def configure_logger(shared_processors: List):
    """Configure the logger with shared processors."""
    basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=DEBUG,
    )
    setup_processors(shared_processors)
    configure(
        context_class=dict,
        wrapper_class=make_filtering_bound_logger(DEBUG),
        logger_factory=stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )


shared_processors = [
    processors.add_log_level,
    processors.TimeStamper(fmt="ISO"),
    processors.StackInfoRenderer(),
    contextvars.merge_contextvars,
]


def configure_logging_for_api():
    """Configure logging for the API."""
    clear_api_logging()
    configure_logger(shared_processors)


def get_logger(ctx: Optional[str] = None) -> Any:
    """
    Get the API logger with the specified context.

    Args:
        ctx: Context string

    Returns:
        Configured structlog logger
    """
    if ctx is None:
        return get_structlog_logger(context=f"{APP_NAME}::API::ROOT")
    else:
        return get_structlog_logger(context=f"{APP_NAME}::API::{ctx}")
