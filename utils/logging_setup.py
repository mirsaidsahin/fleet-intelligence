"""Logging with secret redaction. Technical details go to logs/app.log, not the UI."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Iterable

from utils.config import PROJECT_ROOT

LOGGER_ROOT = "fleet"
_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_MARK = "_fi_handler"


class RedactingFormatter(logging.Formatter):
    """Replaces known secrets in the fully formatted record, tracebacks included."""

    def __init__(self, fmt: str, secrets: Iterable[str] = ()) -> None:
        super().__init__(fmt)
        self._secrets = tuple(s for s in secrets if s)

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        for secret in self._secrets:
            text = text.replace(secret, "***")
        return text


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"{LOGGER_ROOT}.{name}")


def configure_logging(level: str = "INFO", secrets: Iterable[str] = (), log_dir: Path | None = None) -> None:
    """Idempotent setup: safe to call again after a Streamlit rerun."""
    logger = logging.getLogger(LOGGER_ROOT)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    for handler in list(logger.handlers):
        if getattr(handler, _MARK, False):
            logger.removeHandler(handler)
            handler.close()

    formatter = RedactingFormatter(_FORMAT, secrets)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    directory = log_dir or (PROJECT_ROOT / "logs")
    try:
        directory.mkdir(parents=True, exist_ok=True)
        handlers.append(RotatingFileHandler(directory / "app.log", maxBytes=512_000, backupCount=3, encoding="utf-8"))
    except OSError:
        pass  # read-only location: console logging only
    for handler in handlers:
        handler.setFormatter(formatter)
        setattr(handler, _MARK, True)
        logger.addHandler(handler)
