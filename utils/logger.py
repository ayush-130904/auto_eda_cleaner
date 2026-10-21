"""
Centralized logging setup.

Why a dedicated logger module instead of print()?
- print() output disappears once Streamlit's terminal scrolls away and
  gives no timestamp, level, or source module.
- logging lets us filter by severity (DEBUG vs ERROR), write to a file
  for post-mortem debugging, and keep a consistent format everywhere.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str, logs_dir: Path, level: str = "INFO") -> logging.Logger:
    """
    Return a configured logger for `name` (conventionally __name__ of
    the calling module, e.g. "modules.cleaner").

    Safe to call repeatedly with the same name: Python's logging module
    caches loggers by name, and we guard against adding duplicate
    handlers on Streamlit reruns.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level.upper())

    # Streamlit re-executes the whole script on every user interaction.
    # Without this guard, get_logger() would attach a new handler each
    # rerun, and every log line would print N times after N reruns.
    if logger.handlers:
        return logger

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Console handler — visible in the terminal / Render logs.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating file handler — keeps logs on disk for debugging without
    # letting a single log file grow unbounded. maxBytes=2MB, keep 5
    # backups, so worst case ~10MB of log history.
    logs_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        logs_dir / "app.log", maxBytes=2_000_000, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Prevent double-logging via the root logger's own handlers.
    logger.propagate = False

    return logger
