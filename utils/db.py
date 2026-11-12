"""Database access: one pooled engine, a truthful connection check, safe read and write helpers."""
from __future__ import annotations

import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator, Mapping

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

from models.health import ConnectionStatus
from utils.config import Settings
from utils.db_errors import describe_db_error, is_connection_error
from utils.logging_setup import get_logger
from utils.sql_guard import assert_read_only

logger = get_logger("db")


class DatabaseUnavailableError(Exception):
    """The server could not be reached or dropped the connection. Message is UI-safe."""


class QueryError(Exception):
    """A statement failed. Message is UI-safe; details are in the log."""


class Database:
    """Wraps a SQLAlchemy engine. Creating it opens no connection."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @classmethod
    def from_settings(cls, settings: Settings) -> "Database":
        engine = create_engine(
            settings.sqlalchemy_url(),
            pool_size=settings.pool_size,
            max_overflow=2,
            pool_pre_ping=True,  # replaces dead pooled connections instead of failing the page
            pool_recycle=1800,
            connect_args={
                "connect_timeout": settings.connect_timeout,
                "read_timeout": 30,
                "write_timeout": 30,
            },
        )
        logger.info("Engine created for %s", settings.safe_dsn())
        return cls(engine)

    @property
    def engine(self) -> Engine:
        return self._engine

    def ping(self) -> ConnectionStatus:
        """Open a real connection and run a query. Never raises; reports what happened."""
        started = time.perf_counter()
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                if conn.dialect.name == "mysql":
                    database = conn.execute(text("SELECT DATABASE()")).scalar()
                else:
                    database = self._engine.url.database
            latency = round((time.perf_counter() - started) * 1000, 1)
            info = self._engine.dialect.server_version_info
            version = ".".join(str(part) for part in info) if info else None
            return ConnectionStatus(True, datetime.now().astimezone(), latency, version, database)
        except Exception as exc:  # boundary: a failed check is a result, not a crash
            logger.error("Connection check failed: %s", exc, exc_info=True)
            return ConnectionStatus(False, datetime.now().astimezone(), error=describe_db_error(exc))

    def fetch_all(self, sql: str, params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        """Run one read-only, parameterized query and return rows as dicts."""
        assert_read_only(sql)
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(sql), dict(params or {}))
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as exc:
            raise self._wrap(exc) from exc

    def fetch_one(self, sql: str, params: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
        """Return the first result row, or None when the query matched nothing."""
        rows = self.fetch_all(sql, params)
        return rows[0] if rows else None

    @contextmanager
    def transaction(self) -> Iterator[Connection]:
        """Commit on success, roll back on any error. Used by write repositories from Phase 3."""
        try:
            with self._engine.begin() as conn:
                yield conn
        except SQLAlchemyError as exc:
            raise self._wrap(exc) from exc

    def dispose(self) -> None:
        """Close pooled connections when the application shuts down."""
        self._engine.dispose()

    @staticmethod
    def _wrap(exc: SQLAlchemyError) -> Exception:
        """Log the driver detail and return a user-safe application exception."""
        logger.error("Database error: %s", exc, exc_info=True)
        message = describe_db_error(exc)
        return DatabaseUnavailableError(message) if is_connection_error(exc) else QueryError(message)
