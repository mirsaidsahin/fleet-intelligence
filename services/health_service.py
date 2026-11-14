"""Builds the HealthReport shown in the status bar and System page."""
from __future__ import annotations

from typing import Protocol

from models.health import ConnectionStatus, HealthReport, SchemaCheckResult


class _Pingable(Protocol):
    """Minimal interface required to perform a database connection check."""

    def ping(self) -> ConnectionStatus: ...


class _Verifiable(Protocol):
    """Minimal interface required to check database schema metadata."""

    def verify(self) -> SchemaCheckResult: ...


class HealthService:
    """Coordinate connection and schema checks into one immutable report."""

    def __init__(self, database: _Pingable, verifier: _Verifiable) -> None:
        self._database = database
        self._verifier = verifier

    def check(self, previous: HealthReport | None = None, *, verify_schema: bool = True) -> HealthReport:
        """Ping the database and, when connected, optionally re-verify the schema.

        last_success_at is carried forward across failed checks so the UI can say
        when the database last answered. The schema result is never invented: it
        stays None until a check has actually run.
        """
        status = self._database.ping()
        # Preserve the last successful timestamp if this ping fails.
        last_success = status.checked_at if status.connected else (previous.last_success_at if previous else None)

        # Carry forward an old schema result until a requested check replaces it.
        schema: SchemaCheckResult | None = previous.schema if previous else None
        if status.connected and (verify_schema or schema is None):
            schema = self._verifier.verify()
        return HealthReport(connection=status, schema=schema, last_success_at=last_success)
