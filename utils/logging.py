"""Centralized application logging.

Separates training logs from application logs and never logs raw camera frames
or sensitive user information.
"""

from __future__ import annotations

import logging
from pathlib import Path


def get_logger(name: str, log_file: str | Path | None = None, level: int = logging.INFO) -> logging.Logger:
    """Create or retrieve a configured logger.

    Args:
        name: Logger name, typically __name__.
        log_file: Optional file path to also write logs to.
        level: Logging level.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger


def get_training_logger(log_file: str | Path = "outputs/logs/training.log") -> logging.Logger:
    return get_logger("training", log_file=log_file)


def get_app_logger(log_file: str | Path = "outputs/logs/app.log") -> logging.Logger:
    return get_logger("app", log_file=log_file)
