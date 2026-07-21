"""
Nyaya-ZTA Structured Logging
=============================

Provides structured JSON logging with correlation IDs for request tracing.
Every log entry includes:
  - timestamp (ISO 8601)
  - level
  - logger name
  - message
  - correlation_id (when within a request context)
  - extra fields (module, function, etc.)

Usage:
    from app.core.logging import get_logger

    logger = get_logger(__name__)
    logger.info("Processing case", extra={"case_id": "abc-123"})
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Context variable for request correlation ID — set per-request in middleware
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


class StructuredJSONFormatter(logging.Formatter):
    """
    Custom log formatter that outputs structured JSON.

    Each log record is serialized as a single JSON line containing:
    - timestamp, level, logger, message, correlation_id
    - Any extra fields passed via the `extra` parameter
    - Exception info (if present)
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Attach correlation ID from context
        cid = correlation_id_var.get()
        if cid:
            log_entry["correlation_id"] = cid

        # Attach extra fields (excluding standard LogRecord attributes)
        standard_attrs = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                try:
                    json.dumps(value)  # ensure serializable
                    log_entry[key] = value
                except (TypeError, ValueError):
                    log_entry[key] = str(value)

        # Attach exception info
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, default=str)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable formatter for development.

    Outputs colored, aligned log lines with optional correlation IDs.
    """

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        cid = correlation_id_var.get()
        cid_str = f" [{cid[:8]}]" if cid else ""

        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
        msg = record.getMessage()

        formatted = (
            f"{color}{timestamp} {record.levelname:<8}{self.RESET}"
            f"{cid_str} {record.name}: {msg}"
        )

        if record.exc_info and record.exc_info[1]:
            formatted += f"\n  Exception: {record.exc_info[1]}"

        return formatted


def setup_logging(level: str = "INFO", json_output: bool = False) -> None:
    """
    Configure the root logger for the application.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_output: If True, use structured JSON format; otherwise, use
                     human-readable colored format (for development).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicate output
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    if json_output:
        handler.setFormatter(StructuredJSONFormatter())
    else:
        handler.setFormatter(DevelopmentFormatter())

    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger for a module.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)
