"""Job rules: derived truck/driver status, status transitions and assignment scheduling.

Operational status vocabulary: see docs/DEFINITIONS.md. The database has no
status column on trucks or drivers, so status is computed from jobs.Status,
jobs.StartDate and routes.EstimatedHours. Priority:
Conflict > In Transit > Needs Review > Scheduled > Available.

Job status changes and assignment overlap checks follow the same open-job rules.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from itertools import pairwise
from typing import Any


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


PENDING = "Pending"
IN_TRANSIT = "In Transit"
# Only these job states consume a truck or driver in the derived status model.
OPEN_STATUSES = (PENDING, IN_TRANSIT)


def _window(job: OpenJob, now: datetime) -> tuple[datetime, datetime] | None:
    """Time span a job occupies, or None when its start date is unknown.

    An In Transit job has no end date on record, so it occupies the truck until
    at least `now` even when it has outrun its estimate.
    """
    if job.start is None:
        return None
    end = job.start + timedelta(hours=job.estimated_hours or 0)
    if job.status == IN_TRANSIT:
        end = max(end, now)
    return job.start, end


def _has_conflict(jobs: list[OpenJob], now: datetime) -> bool:
    """Detect duplicate transit assignments or overlapping estimated time windows."""
    # Two simultaneous trips cannot be valid for the same truck or driver.
    if sum(1 for j in jobs if j.status == IN_TRANSIT) > 1:
        return True
    # Sort known windows so adjacent comparisons can detect any overlap.
    windows = sorted(w for w in (_window(j, now) for j in jobs) if w is not None)
    return any(nxt_start < cur_end for (_, cur_end), (nxt_start, _) in pairwise(windows))


def classify(open_jobs: Iterable[OpenJob], now: datetime) -> OperationalStatus:
    """Status for one truck (jobs grouped by TruckID) or one driver (grouped by DriverID).

    `now` and job dates must both be naive or both timezone-aware.
    """
    jobs = [j for j in open_jobs if j.status in OPEN_STATUSES]
    if not jobs:
        return OperationalStatus.AVAILABLE
    if _has_conflict(jobs, now):
        return OperationalStatus.CONFLICT
    if any(j.status == IN_TRANSIT for j in jobs):
        return OperationalStatus.IN_TRANSIT
    if any(j.start is not None and j.start < now for j in jobs):
        return OperationalStatus.NEEDS_REVIEW
    return OperationalStatus.SCHEDULED


# Keep the state machine explicit so unsupported jumps are rejected consistently.
ALLOWED_STATUS_TRANSITIONS = {
    "Pending": {"Pending", "In Transit", "Cancelled"},
    "In Transit": {"In Transit", "Completed", "Cancelled"},
    "Completed": {"Completed"},
    "Cancelled": {"Cancelled"},
}


def status_transition_problem(previous: str | None, following: str | None) -> str | None:
    """Return a user-facing reason when a job status change is not allowed."""
    # New or legacy rows without a prior status have no known transition to enforce.
    if previous is None or following is None or following in ALLOWED_STATUS_TRANSITIONS.get(previous, set()):
        return None
    # Exclude the current value so the message lists only meaningful next actions.
    allowed = ", ".join(sorted(ALLOWED_STATUS_TRANSITIONS.get(previous, set()) - {previous})) or "no further status"
    return f"A job cannot move from {previous} to {following}. Allowed next status: {allowed}."


def _interval(start: datetime | None, hours: float, status: str, now: datetime) -> tuple[datetime, datetime] | None:
    """Build the estimated job window, or return None when it cannot be timed."""
    if start is None:
        return None
    # SQLite integration tests return ISO strings; MySQL normally returns datetimes.
    if isinstance(start, str):
        start = datetime.fromisoformat(start)
    # Clamp malformed negative estimates to zero rather than reversing the window.
    end = start + timedelta(hours=max(0.0, hours))
    # An in-transit job remains occupied at least until the current time.
    if status == "In Transit":
        end = max(end, now)
    return start, end


def find_assignment_conflicts(
    values: Mapping[str, Any], existing_jobs: Sequence[Mapping[str, Any]],
    route_hours: float, now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Find overlapping active jobs sharing the selected truck or driver."""
    # Closed jobs do not reserve a truck or driver.
    if values.get("Status") not in OPEN_STATUSES:
        return []
    now = now or datetime.now()
    candidate_start = values.get("StartDate")
    # Treat an undated in-transit assignment as starting now for conflict checks.
    if values.get("Status") == "In Transit" and candidate_start is None:
        candidate_start = now
    candidate = _interval(candidate_start, route_hours, values["Status"], now)
    conflicts = []
    for job in existing_jobs:
        # Ignore historical/cancelled jobs and unrelated vehicle/driver pairs.
        if job.get("Status") not in OPEN_STATUSES:
            continue
        shares_assignment = (
            job.get("TruckID") == values.get("TruckID")
            or job.get("DriverID") == values.get("DriverID")
        )
        if not shares_assignment:
            continue
        existing = _interval(job.get("StartDate"), float(job.get("EstimatedHours") or 0), job["Status"], now)
        # Unknown timing is risky when either side is already in transit.
        if candidate is None or existing is None:
            if "In Transit" in (values.get("Status"), job["Status"]):
                conflicts.append(dict(job))
            continue
        # Strict comparisons allow back-to-back assignments that touch at one endpoint.
        if candidate[0] < existing[1] and existing[0] < candidate[1]:
            conflicts.append(dict(job))
    return conflicts
