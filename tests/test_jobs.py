from datetime import datetime, timedelta

import pytest

from services.jobs import (
    OpenJob,
    OperationalStatus as S,
    classify,
    find_assignment_conflicts,
    status_transition_problem,
)

NOW = datetime(2026, 10, 29, 12, 0)


def job(job_id, status, start, hours=2.0):
    return OpenJob(job_id, status, start, hours)


def test_no_open_jobs_is_available():
    assert classify([], NOW) is S.AVAILABLE


def test_completed_and_cancelled_jobs_are_ignored():
    jobs = [job(1, "Completed", NOW - timedelta(days=3)), job(2, "Cancelled", NOW - timedelta(days=2))]
    assert classify(jobs, NOW) is S.AVAILABLE


def test_pending_in_the_future_is_scheduled_not_available():
    assert classify([job(1, "Pending", NOW + timedelta(days=2))], NOW) is S.SCHEDULED


def test_pending_with_passed_start_needs_review():
    assert classify([job(44, "Pending", NOW - timedelta(days=35))], NOW) is S.NEEDS_REVIEW


def test_in_transit_alone_is_in_transit_even_when_overdue():
    assert classify([job(42, "In Transit", NOW - timedelta(days=44), 0.6)], NOW) is S.IN_TRANSIT


def test_in_transit_with_later_pending_job_is_in_transit():
    jobs = [job(1, "In Transit", NOW - timedelta(hours=1), 3.0), job(2, "Pending", NOW + timedelta(days=1))]
    assert classify(jobs, NOW) is S.IN_TRANSIT


def test_pending_start_inside_running_job_window_is_conflict():
    jobs = [job(1, "In Transit", NOW - timedelta(hours=1), 3.0), job(2, "Pending", NOW + timedelta(hours=1))]
    assert classify(jobs, NOW) is S.CONFLICT


def test_overdue_in_transit_overlaps_stale_pending_job():
    jobs = [job(42, "In Transit", NOW - timedelta(days=44), 0.6), job(50, "Pending", NOW - timedelta(days=19))]
    assert classify(jobs, NOW) is S.CONFLICT


def test_two_in_transit_jobs_are_a_conflict():
    jobs = [job(1, "In Transit", NOW - timedelta(days=1)), job(2, "In Transit", NOW - timedelta(days=2))]
    assert classify(jobs, NOW) is S.CONFLICT


def test_back_to_back_pending_jobs_do_not_conflict():
    jobs = [job(1, "Pending", NOW + timedelta(days=1), 2.0), job(2, "Pending", NOW + timedelta(days=1, hours=2), 2.0)]
    assert classify(jobs, NOW) is S.SCHEDULED


def test_overlapping_pending_jobs_conflict_even_when_nested():
    start = NOW + timedelta(days=1)
    jobs = [job(1, "Pending", start, 10.0), job(2, "Pending", start + timedelta(hours=1), 1.0), job(3, "Pending", start + timedelta(hours=4), 1.0)]
    assert classify(jobs, NOW) is S.CONFLICT


def test_pending_without_start_date_is_scheduled_and_skipped_for_overlap():
    jobs = [job(1, "Pending", None), job(2, "Pending", NOW + timedelta(days=1))]
    assert classify(jobs, NOW) is S.SCHEDULED

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


WORKFLOW_NOW = datetime(2026, 11, 12, 12)


def make_job(job_id=9, status="Pending", start=None, truck=1, driver=2, hours=2):
    return {"JobID": job_id, "Status": status, "StartDate": start,
            "TruckID": truck, "DriverID": driver, "EstimatedHours": hours}


def candidate(start, truck=1, driver=2, status="Pending"):
    return {"Status": status, "StartDate": start, "TruckID": truck,
            "DriverID": driver}


def test_assignment_conflict_detects_shared_truck_overlap():
    conflict = make_job(start=WORKFLOW_NOW + timedelta(hours=1), driver=88)
    found = find_assignment_conflicts(candidate(WORKFLOW_NOW), [conflict], 2, WORKFLOW_NOW)
    assert [job["JobID"] for job in found] == [9]


def test_assignment_conflict_detects_shared_driver_overlap():
    conflict = make_job(start=WORKFLOW_NOW + timedelta(hours=1), truck=88)
    found = find_assignment_conflicts(candidate(WORKFLOW_NOW), [conflict], 2, WORKFLOW_NOW)
    assert [job["JobID"] for job in found] == [9]


def test_back_to_back_jobs_and_unrelated_assignments_are_allowed():
    next_job = make_job(start=WORKFLOW_NOW + timedelta(hours=2), driver=88)
    unrelated = make_job(job_id=10, start=WORKFLOW_NOW, truck=88, driver=89)
    assert find_assignment_conflicts(candidate(WORKFLOW_NOW), [next_job, unrelated], 2, WORKFLOW_NOW) == []


def test_missing_start_is_conflict_with_current_transit_job():
    transit = make_job(status="In Transit", start=WORKFLOW_NOW - timedelta(hours=1))
    assert find_assignment_conflicts(candidate(None), [transit], 2, WORKFLOW_NOW) == [transit]


def test_undated_transit_assignment_conflicts_with_other_open_assignment():
    undated = make_job(status="Pending", start=None)
    proposed_transit = candidate(None, status="In Transit")
    assert find_assignment_conflicts(proposed_transit, [undated], 2, WORKFLOW_NOW) == [undated]


def test_completed_or_cancelled_jobs_do_not_block_assignment():
    old = make_job(status="Completed", start=WORKFLOW_NOW)
    cancelled = make_job(job_id=10, status="Cancelled", start=WORKFLOW_NOW)
    assert find_assignment_conflicts(candidate(WORKFLOW_NOW), [old, cancelled], 2, WORKFLOW_NOW) == []
