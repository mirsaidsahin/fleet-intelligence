"""Business rules for job status changes and assignment scheduling."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Mapping, Sequence

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
    if values.get("Status") not in ("Pending", "In Transit"):
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
        if job.get("Status") not in ("Pending", "In Transit"):
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
