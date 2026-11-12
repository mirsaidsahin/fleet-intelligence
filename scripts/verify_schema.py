"""Read-only check of the live MySQL database against the expected omnilogistics schema.

Usage:  python scripts/verify_schema.py
Exit codes: 0 matches, 1 schema differs, 2 not configured or not reachable.
Only SELECT and metadata queries are issued. Nothing is created, changed or dropped.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.schema_spec import REFERENCE_ROW_COUNTS  # noqa: E402
from services.schema_verifier import SchemaVerifier  # noqa: E402
from utils.config import ConfigError, load_settings  # noqa: E402
from utils.db import Database, DatabaseUnavailableError, QueryError  # noqa: E402
from utils.logging_setup import configure_logging  # noqa: E402


def main() -> int:
    """Check configuration, connectivity, expected schema, and reference counts."""
    try:
        settings = load_settings()
    except ConfigError as exc:
        print("Configuration problem:")
        for problem in exc.problems:
            print(f"  - {problem}")
        print("Copy .env.example to .env and fill in the values.")
        return 2

    configure_logging(settings.log_level, settings.secrets())
    print(f"Target: {settings.safe_dsn()}")

    db = Database.from_settings(settings)
    status = db.ping()
    if not status.connected:
        print(f"Connection FAILED: {status.error}")
        return 2
    print(f"Connected to '{status.database}', MySQL {status.server_version}, {status.latency_ms} ms")

    result = SchemaVerifier(db.engine).verify()
    print(f"Tables {result.tables_found}/{result.tables_expected}, views {result.views_found}/{result.views_expected}, "
          f"foreign keys {result.foreign_keys_found}/{result.foreign_keys_expected}")
    for problem in result.problems():
        print(f"  - {problem}")

    print("\nRow counts (reference values are from the 2026-10-29 dump; live data may differ):")
    for table, reference in REFERENCE_ROW_COUNTS.items():
        # Report live row counts as informational comparisons, not schema failures.
        try:
            row = db.fetch_one(f"SELECT COUNT(*) AS n FROM {table}")
            live = row["n"] if row else "?"
        except (DatabaseUnavailableError, QueryError) as exc:
            live = f"error ({exc})"
        print(f"  {table:<10} live {live!s:<6} reference {reference}")

    print("\nResult:", "schema matches" if result.ok else "schema differs")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
