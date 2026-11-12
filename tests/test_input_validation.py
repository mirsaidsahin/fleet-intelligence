from datetime import datetime, timedelta

import pytest

from components.entity_manager import FIELDS
from services.input_validation import validate_record


@pytest.mark.parametrize("table,values,expected", [
    ("brands", {"BrandName": "  "}, "BrandName is required."),
    ("garages", {"City": "Turku", "Capacity": -1}, "Capacity cannot be negative."),
    ("routes", {"DepartureCity": "A", "ArrivalCity": "B", "DistanceKm": 1.5, "EstimatedHours": 2}, "DistanceKm must be a whole number."),
])
def test_reports_required_and_invalid_numeric_fields(table, values, expected):
    assert expected in validate_record(table, values, FIELDS)


def test_job_end_cannot_precede_start():
    start = datetime(2026, 11, 12, 12)
    problems = validate_record("jobs", {"StartDate": start, "EndDate": start - timedelta(minutes=1)}, FIELDS)
    assert "EndDate must be the same as or later than StartDate." in problems


def test_optional_values_and_valid_job_dates_pass():
    start = datetime(2026, 11, 12, 12)
    values = {name: None for name, _, _ in FIELDS["jobs"]}
    values.update(StartDate=start, EndDate=start, Status="Completed")
    assert validate_record("jobs", values, FIELDS) == []


def test_unknown_record_type_is_rejected():
    assert validate_record("secret_table", {}, FIELDS) == ["Unsupported record type."]
