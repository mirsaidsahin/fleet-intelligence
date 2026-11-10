from datetime import datetime, timedelta

from models.status import OpenJob, OperationalStatus as S
from services.fleet_status import classify
from services.visual_config import VisualConfig, choose_visual_config

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


def test_trailer_image_only_for_ce_truck_with_in_transit_job():
    assert choose_visual_config("CE", True) is VisualConfig.TRACTOR_WITH_TRAILER
    assert choose_visual_config("ce", True) is VisualConfig.TRACTOR_WITH_TRAILER
    assert choose_visual_config("CE", False) is VisualConfig.TRACTOR_ONLY
    assert choose_visual_config("C", True) is VisualConfig.TRACTOR_ONLY
    assert choose_visual_config(None, True) is VisualConfig.TRACTOR_ONLY
