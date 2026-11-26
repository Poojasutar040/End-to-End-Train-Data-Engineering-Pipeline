"""Centralized logging configuration for backend, ETL, ML, and dashboard modules."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from utils.config import PATHS


def get_logger(name: str, log_file: Path | None = None) -> logging.Logger:
    """Return a configured logger writing to console and rotating/appending log file."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    target_log = log_file or (PATHS.logs_dir / "railway_pipeline.log")
    target_log.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(target_log, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger
