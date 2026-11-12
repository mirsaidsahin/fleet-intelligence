"""Business rules for job status changes and assignment scheduling."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Mapping, Sequence

ALLOWED_STATUS_TRANSITIONS = {
    "Pending": {"Pending", "In Transit", "Cancelled"},
    "In Transit": {"In Transit", "Completed", "Cancelled"},
    "Completed": {"Completed"},
    "Cancelled": {"Cancelled"},
}


def status_transition_problem(previous: str | None, following: str | None) -> str | None:
    """Return a user-facing reason when a job status change is not allowed."""
    if previous is None or following is None or following in ALLOWED_STATUS_TRANSITIONS.get(previous, set()):
        return None
    allowed = ", ".join(sorted(ALLOWED_STATUS_TRANSITIONS.get(previous, set()) - {previous})) or "no further status"
    return f"A job cannot move from {previous} to {following}. Allowed next status: {allowed}."


def _interval(start: datetime | None, hours: float, status: str, now: datetime) -> tuple[datetime, datetime] | None:
    if start is None:
        return None
    if isinstance(start, str):
        start = datetime.fromisoformat(start)
    end = start + timedelta(hours=max(0.0, hours))
    if status == "In Transit":
        end = max(end, now)
    return start, end


def find_assignment_conflicts(
    values: Mapping[str, Any], existing_jobs: Sequence[Mapping[str, Any]],
    route_hours: float, now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Find overlapping active jobs sharing the selected truck or driver."""
    if values.get("Status") not in ("Pending", "In Transit"):
        return []
    now = now or datetime.now()
    candidate_start = values.get("StartDate")
    if values.get("Status") == "In Transit" and candidate_start is None:
        candidate_start = now
    candidate = _interval(candidate_start, route_hours, values["Status"], now)
    conflicts = []
    for job in existing_jobs:
        if job.get("Status") not in ("Pending", "In Transit"):
            continue
        shares_assignment = (
            job.get("TruckID") == values.get("TruckID")
            or job.get("DriverID") == values.get("DriverID")
        )
        if not shares_assignment:
            continue
        existing = _interval(job.get("StartDate"), float(job.get("EstimatedHours") or 0), job["Status"], now)
        if candidate is None or existing is None:
            if "In Transit" in (values.get("Status"), job["Status"]):
                conflicts.append(dict(job))
            continue
        if candidate[0] < existing[1] and existing[0] < candidate[1]:
            conflicts.append(dict(job))
    return conflicts
