"""
Logging Configuration.

Provides a centralized logging configuration for the enterprise platform,
handling log file rotation, console stdout, and context-based Request ID correlation.
"""

import logging
import os
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from typing import Optional
from src.core.config import settings

# Context variable to hold the Request ID (Correlation ID) across the current execution flow.
request_id_ctx_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class RequestIdFormatter(logging.Formatter):
    """
    Custom Formatter targeting context-aware formatting.
    
    Extracts the current request ID from contextvars and interpolates it
    into the log format structure automatically.
    """

    def format(self, record: logging.LogRecord) -> str:
        record.request_id = request_id_ctx_var.get() or "SYS"
        return super().format(record)


def setup_logging() -> None:
    """
    Configures application-wide logging.
    
    Creates a rotating file handler inside a project-relative `logs/` directory
    and a stream handler targeting standard output.
    """
    # Create logs directory inside workspace root if not existing
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_filepath = os.path.join(log_dir, "app.log")

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Log record pattern configuration
    log_format = "%(asctime)s | %(levelname)-8s | [%(request_id)s] | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    formatter = RequestIdFormatter(log_format)

    # Retrieve root logger and establish configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers by clearing out previous handlers
    root_logger.handlers = []

    # 1. Console Stream Handler (Standard Out - optimal for AWS CloudWatch / Container logging)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # 2. Local Rotating File Handler for persistence checks
    file_handler = RotatingFileHandler(
        filename=log_filepath,
        maxBytes=10 * 1024 * 1024,  # 10 MB limit per file
        backupCount=5,              # Retain last 5 archives
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)

    # Suppress noise from third party dependency packages in the logger
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    root_logger.info("Logging infrastructure successfully initialized.")
