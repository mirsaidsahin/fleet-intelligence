"""Operational status vocabulary for trucks and drivers. See docs/DEFINITIONS.md."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OperationalStatus(str, Enum):
    AVAILABLE = "Available"
    SCHEDULED = "Scheduled"
    NEEDS_REVIEW = "Needs Review"
    IN_TRANSIT = "In Transit"
    CONFLICT = "Conflict"


@dataclass(frozen=True)
class OpenJob:
    """A job that is Pending or In Transit, with the route's estimated duration."""

    job_id: int
    status: str  # 'Pending' or 'In Transit'
    start: datetime | None
    estimated_hours: float | None
