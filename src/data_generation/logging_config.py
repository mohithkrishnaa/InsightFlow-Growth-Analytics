# Logging Configuration for the InsightFlow Data Generation Pipeline

import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Sets up application-wide logging with Console and File handlers.
    Creates a 'logs/' directory in the workspace if not already present.
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "pipeline.log")

    # Map string log level to python logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)

    logger = logging.getLogger("InsightFlowGenerator")
    logger.setLevel(level)

    # Prevent duplicate handlers if setup is called multiple times
    if logger.handlers:
        return logger

    # Formatter for structured logs
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File Handler (with size-based rotation: max 5MB, keep 3 backup logs)
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
