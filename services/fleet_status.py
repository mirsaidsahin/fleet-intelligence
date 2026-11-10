"""Derives a truck's or driver's displayed status from its open jobs.

The database has no status column on trucks or drivers, so status is computed
from jobs.Status, jobs.StartDate and routes.EstimatedHours. Priority:
Conflict > In Transit > Needs Review > Scheduled > Available.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from models.status import OpenJob, OperationalStatus

PENDING = "Pending"
IN_TRANSIT = "In Transit"
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
    if sum(1 for j in jobs if j.status == IN_TRANSIT) > 1:
        return True
    windows = sorted(w for w in (_window(j, now) for j in jobs) if w is not None)
    return any(nxt_start < cur_end for (_, cur_end), (nxt_start, _) in zip(windows, windows[1:]))


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
