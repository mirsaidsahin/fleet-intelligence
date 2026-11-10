"""Builds the HealthReport shown in the status bar and System page."""
from __future__ import annotations

from typing import Any, Protocol

from models.health import ConnectionStatus, HealthReport, SchemaCheckResult


class _Pingable(Protocol):
    def ping(self) -> ConnectionStatus: ...


class _Verifiable(Protocol):
    def verify(self) -> SchemaCheckResult: ...


class HealthService:
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
        last_success = status.checked_at if status.connected else (previous.last_success_at if previous else None)

        schema: SchemaCheckResult | None = previous.schema if previous else None
        if status.connected and (verify_schema or schema is None):
            schema = self._verifier.verify()
        return HealthReport(connection=status, schema=schema, last_success_at=last_success)
