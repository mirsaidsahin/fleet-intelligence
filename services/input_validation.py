"""Validation for fleet record forms, kept independent of Streamlit."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


def validate_record(table: str, values: Mapping[str, Any], fields: Mapping[str, list[tuple[str, str, bool]]]) -> list[str]:
    """Return actionable validation messages for a record; an empty list is valid."""
    if table not in fields:
        return ["Unsupported record type."]

    problems: list[str] = []
    for name, kind, nullable in fields[table]:
        value = values.get(name)
        if not nullable and kind == "text" and (value is None or not str(value).strip()):
            problems.append(f"{name} is required.")
        elif kind in ("int", "decimal") and value is not None:
            try:
                number = float(value)
            except (TypeError, ValueError):
                problems.append(f"{name} must be a number.")
                continue
            if number < 0:
                problems.append(f"{name} cannot be negative.")
            elif kind == "int" and not number.is_integer():
                problems.append(f"{name} must be a whole number.")

    if table == "jobs":
        start, end = values.get("StartDate"), values.get("EndDate")
        if start is not None and end is not None and end < start:
            problems.append("EndDate must be the same as or later than StartDate.")

    return problems
