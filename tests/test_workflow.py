from datetime import datetime, timedelta

import pytest

from services.workflow import find_assignment_conflicts, status_transition_problem


@pytest.mark.parametrize("previous,following", [
    ("Pending", "Pending"), ("Pending", "In Transit"), ("Pending", "Cancelled"),
    ("In Transit", "In Transit"), ("In Transit", "Completed"), ("In Transit", "Cancelled"),
    ("Completed", "Completed"), ("Cancelled", "Cancelled"),
])
def test_allowed_job_status_transitions(previous, following):
    assert status_transition_problem(previous, following) is None


@pytest.mark.parametrize("previous,following", [
    ("Pending", "Completed"), ("In Transit", "Pending"),
    ("Completed", "Pending"), ("Cancelled", "In Transit"),
])
def test_terminal_or_invalid_job_status_transitions_are_rejected(previous, following):
    assert "cannot move" in status_transition_problem(previous, following)


NOW = datetime(2026, 11, 12, 12)


def make_job(job_id=9, status="Pending", start=None, truck=1, driver=2, hours=2):
    return {"JobID": job_id, "Status": status, "StartDate": start,
            "TruckID": truck, "DriverID": driver, "EstimatedHours": hours}


def candidate(start, truck=1, driver=2, status="Pending"):
    return {"Status": status, "StartDate": start, "TruckID": truck,
            "DriverID": driver}


def test_assignment_conflict_detects_shared_truck_overlap():
    conflict = make_job(start=NOW + timedelta(hours=1), driver=88)
    found = find_assignment_conflicts(candidate(NOW), [conflict], 2, NOW)
    assert [job["JobID"] for job in found] == [9]


def test_assignment_conflict_detects_shared_driver_overlap():
    conflict = make_job(start=NOW + timedelta(hours=1), truck=88)
    found = find_assignment_conflicts(candidate(NOW), [conflict], 2, NOW)
    assert [job["JobID"] for job in found] == [9]


def test_back_to_back_jobs_and_unrelated_assignments_are_allowed():
    next_job = make_job(start=NOW + timedelta(hours=2), driver=88)
    unrelated = make_job(job_id=10, start=NOW, truck=88, driver=89)
    assert find_assignment_conflicts(candidate(NOW), [next_job, unrelated], 2, NOW) == []


def test_missing_start_is_conflict_with_current_transit_job():
    transit = make_job(status="In Transit", start=NOW - timedelta(hours=1))
    assert find_assignment_conflicts(candidate(None), [transit], 2, NOW) == [transit]


def test_undated_transit_assignment_conflicts_with_other_open_assignment():
    undated = make_job(status="Pending", start=None)
    proposed_transit = candidate(None, status="In Transit")
    assert find_assignment_conflicts(proposed_transit, [undated], 2, NOW) == [undated]


def test_completed_or_cancelled_jobs_do_not_block_assignment():
    old = make_job(status="Completed", start=NOW)
    cancelled = make_job(job_id=10, status="Cancelled", start=NOW)
    assert find_assignment_conflicts(candidate(NOW), [old, cancelled], 2, NOW) == []
