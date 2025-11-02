"""Centralized logging configuration and helpers."""

from __future__ import annotations

import logging
import os
import sys
from typing import Optional

_CONFIGURED = False


def _resolve_level(level: Optional[str]) -> str:
    env_level = level or os.getenv("LOG_LEVEL", "INFO")
    return env_level.upper()


def setup_logging(level: Optional[str] = None) -> None:
    """Configure global logging once with a consistent formatter."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    logging.basicConfig(
        level=_resolve_level(level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )
    logging.captureWarnings(True)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger, ensuring logging is configured."""
    setup_logging()
    return logging.getLogger(name)


__all__ = ["get_logger", "setup_logging"]
