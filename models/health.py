"""Plain data objects describing connection and schema health (no framework imports)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ConnectionStatus:
    """One database ping result and its safe, optional diagnostic details."""

    connected: bool
    checked_at: datetime
    latency_ms: float | None = None
    server_version: str | None = None
    database: str | None = None
    error: str | None = None  # short, safe message; raw details go to the log


@dataclass(frozen=True)
class SchemaCheckResult:
    """Counts and differences returned by a comparison with the expected schema."""

    tables_expected: int
    tables_found: int
    views_expected: int
    views_found: int
    foreign_keys_expected: int
    foreign_keys_found: int
    missing_tables: tuple[str, ...] = ()
    missing_columns: tuple[tuple[str, tuple[str, ...]], ...] = ()
    missing_views: tuple[str, ...] = ()
    missing_foreign_keys: tuple[str, ...] = ()
    error: str | None = None

    @property
    def ok(self) -> bool:
        """Return true only when no connection or schema differences were reported."""
        return not (
            self.error
            or self.missing_tables
            or self.missing_columns
            or self.missing_views
            or self.missing_foreign_keys
        )

    def problems(self) -> list[str]:
        """Flatten schema differences into short messages for the system page."""
        out: list[str] = []
        if self.error:
            out.append(self.error)
        out += [f"Missing table: {t}" for t in self.missing_tables]
        out += [f"Missing columns in {t}: {', '.join(cols)}" for t, cols in self.missing_columns]
        out += [f"Missing view: {v}" for v in self.missing_views]
        out += [f"Missing foreign key: {fk}" for fk in self.missing_foreign_keys]
        return out


@dataclass(frozen=True)
class HealthReport:
    """Combine the latest connection check with the last known schema result."""

    connection: ConnectionStatus
    schema: SchemaCheckResult | None  # None until a schema check has run
    last_success_at: datetime | None  # last time a connection check succeeded

    @property
    def refreshed_at(self) -> datetime:
        """Use the connection check time as the report refresh time."""
        return self.connection.checked_at
