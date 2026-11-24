from datetime import datetime, timedelta

import pytest

from services.input_validation import FIELDS, validate_record


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


def test_valid_brand_returns_cleaned_values_without_errors():
    values = {"BrandName": "Volvo", "Country": "Sweden"}

    assert validate_record("brands", values, FIELDS) == []
    assert values == {"BrandName": "Volvo", "Country": "Sweden"}


@pytest.mark.parametrize("title", ["", "   ", "\t  "])
def test_blank_or_whitespace_brand_name_is_rejected(title):
    problems = validate_record("brands", {"BrandName": title}, FIELDS)

    assert "BrandName is required." in problems


@pytest.mark.parametrize("quantity", [-1, -0.25])
def test_negative_cargo_quantity_is_rejected(quantity):
    values = {"CargoName": "Pallets", "WeightKg": quantity, "ValueEUR": 100}

    assert "WeightKg cannot be negative." in validate_record("cargos", values, FIELDS)


@pytest.mark.parametrize("quantity", ["many", object()])
def test_invalid_cargo_quantity_types_are_rejected(quantity):
    values = {"CargoName": "Pallets", "WeightKg": quantity, "ValueEUR": 100}

    problems = validate_record("cargos", values, FIELDS)
    assert "WeightKg must be a number." in problems


def test_non_finite_cargo_quantity_is_rejected():
    values = {"CargoName": "Pallets", "WeightKg": float("nan"), "ValueEUR": 100}

    assert "WeightKg must be a finite number." in validate_record("cargos", values, FIELDS)


def test_job_status_update_must_follow_allowed_workflow():
    values = {name: None for name, _, _ in FIELDS["jobs"]}
    values.update(Status="Completed")
    errors = validate_record("jobs", values, current={"Status": "Pending"})
    assert any("cannot move from Pending to Completed" in error for error in errors)


def test_valid_job_status_transition_passes_validation():
    values = {name: None for name, _, _ in FIELDS["jobs"]}
    values.update(Status="In Transit")
    assert validate_record("jobs", values, current={"Status": "Pending"}) == []
