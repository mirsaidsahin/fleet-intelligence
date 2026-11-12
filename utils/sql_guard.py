"""Safety net for read queries. Parameter binding remains the real SQL-injection defence."""
from __future__ import annotations

import re

_COMMENTS = re.compile(r"(--[^\n]*|#[^\n]*|/\*.*?\*/)", re.S)
# Keep the accepted query starts explicit so write statements fail closed.
_ALLOWED_FIRST = {"SELECT", "WITH", "SHOW", "DESCRIBE", "DESC", "EXPLAIN"}
_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|RENAME)\b", re.I
)


def assert_read_only(sql: str) -> None:
    """Raise ValueError unless `sql` is a single read-only statement."""
    cleaned = _COMMENTS.sub(" ", sql).strip().rstrip(";").strip()
    # Reject empty and multi-statement input before inspecting its command.
    if not cleaned:
        raise ValueError("Empty SQL statement.")
    if ";" in cleaned:
        raise ValueError("Multiple SQL statements are not allowed.")
    first = cleaned.split(None, 1)[0].upper()
    # A read-only start token blocks direct INSERT/UPDATE/DELETE calls.
    if first not in _ALLOWED_FIRST:
        raise ValueError("Only read-only statements may use the read helpers.")
    if _FORBIDDEN.search(cleaned):
        # Also block write keywords hidden inside a WITH query.
        raise ValueError("Statement contains a write or schema keyword.")
