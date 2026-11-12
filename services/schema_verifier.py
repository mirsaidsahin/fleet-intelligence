"""Read-only comparison of the live schema with the expected one."""
from __future__ import annotations

from typing import Any

from models.health import SchemaCheckResult
from models.schema_spec import EXPECTED_SCHEMA, SchemaSpec
from utils.db_errors import describe_db_error
from utils.logging_setup import get_logger

logger = get_logger("schema")


def compare_schema(inspector: Any, spec: SchemaSpec = EXPECTED_SCHEMA) -> SchemaCheckResult:
    """Compare an inspector-like object with `spec`.

    The inspector needs get_table_names, get_view_names, get_columns and
    get_foreign_keys (the SQLAlchemy Inspector API). Names are compared
    case-insensitively.
    """
    actual_tables = {name.lower(): name for name in inspector.get_table_names()}
    # Normalize names so schema checks work across case-sensitive database setups.
    actual_views = {name.lower() for name in inspector.get_view_names()}

    missing_tables: list[str] = []
    missing_columns: list[tuple[str, tuple[str, ...]]] = []
    fk_found = 0
    missing_fks: list[str] = []

    for table, columns in spec.tables.items():
        # Check required tables and columns first to report missing objects clearly.
        real_name = actual_tables.get(table.lower())
        if real_name is None:
            missing_tables.append(table)
            continue
        present = {col["name"].lower() for col in inspector.get_columns(real_name)}
        absent = tuple(col for col in columns if col.lower() not in present)
        if absent:
            missing_columns.append((table, absent))

    fks_by_table: dict[str, set[tuple[str, str, str]]] = {}
    for table in spec.tables:
        real_name = actual_tables.get(table.lower())
        if real_name is None:
            continue
        found: set[tuple[str, str, str]] = set()
        for fk in inspector.get_foreign_keys(real_name):
            for local, remote in zip(fk["constrained_columns"], fk["referred_columns"]):
                found.add((local.lower(), fk["referred_table"].lower(), remote.lower()))
        fks_by_table[table] = found

    fk_expected_checkable = 0
    for fk in spec.foreign_keys:
        # Skip foreign-key checks for missing tables already reported above.
        if fk.table not in fks_by_table:
            continue  # the table itself is already reported as missing
        fk_expected_checkable += 1
        if (fk.column.lower(), fk.ref_table.lower(), fk.ref_column.lower()) in fks_by_table[fk.table]:
            fk_found += 1
        else:
            missing_fks.append(fk.label())

    missing_views = tuple(v for v in spec.views if v.lower() not in actual_views)

    return SchemaCheckResult(
        tables_expected=len(spec.tables),
        tables_found=len(spec.tables) - len(missing_tables),
        views_expected=len(spec.views),
        views_found=len(spec.views) - len(missing_views),
        foreign_keys_expected=len(spec.foreign_keys),
        foreign_keys_found=fk_found,
        missing_tables=tuple(missing_tables),
        missing_columns=tuple(missing_columns),
        missing_views=missing_views,
        missing_foreign_keys=tuple(missing_fks),
    )


class SchemaVerifier:
    """Runs the comparison against a live engine using read-only metadata queries."""

    def __init__(self, engine: Any, spec: SchemaSpec = EXPECTED_SCHEMA) -> None:
        self._engine = engine
        self._spec = spec

    def verify(self) -> SchemaCheckResult:
        """Inspect the configured engine and turn inspection failures into a result."""
        from sqlalchemy import inspect  # lazy: keeps pure logic importable without the driver stack

        try:
            return compare_schema(inspect(self._engine), self._spec)
        except Exception as exc:  # boundary: report as a failed check, never crash the page
            logger.error("Schema verification failed: %s", exc, exc_info=True)
            return SchemaCheckResult(
                tables_expected=len(self._spec.tables),
                tables_found=0,
                views_expected=len(self._spec.views),
                views_found=0,
                foreign_keys_expected=len(self._spec.foreign_keys),
                foreign_keys_found=0,
                error=describe_db_error(exc),
            )
