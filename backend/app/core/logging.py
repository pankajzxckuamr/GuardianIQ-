"""
Logging configuration for GuardianIQ.
Request ID middleware is in core.middleware module.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Ensure logs directory exists before handler creation
os.makedirs("logs", exist_ok=True)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# File handler with rotation
file_handler = RotatingFileHandler(
    "logs/app.log",
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

