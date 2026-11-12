"""Operational status vocabulary for trucks and drivers. See docs/DEFINITIONS.md."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OperationalStatus(str, Enum):
    """Display states derived from open job assignments."""

    AVAILABLE = "Available"
    SCHEDULED = "Scheduled"
    NEEDS_REVIEW = "Needs Review"
    IN_TRANSIT = "In Transit"
    CONFLICT = "Conflict"


@dataclass(frozen=True)
class OpenJob:
    """A job that is Pending or In Transit, with the route's estimated duration."""

    # Preserve the source job ID so conflict explanations can point back to a record.
    job_id: int
    # Keep the raw schema value; the status service applies the recognized open states.
    status: str  # 'Pending' or 'In Transit'
    # A missing start is allowed by the schema and cannot form a time window.
    start: datetime | None
    # The estimate supplies an end time where the database has no actual finish.
    estimated_hours: float | None
