"""Validation for fleet record forms, kept independent of Streamlit."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


FIELDS = {
    "trucks": [("BrandID","brand",True),("Model","text",False),("ProductionYear","int",True),("RequiredLicense","license",False),("PlateNumber","text",False),("Mileage","int",True),("GarageID","garage",True),("AssignedDriverID","driver",True)],
    "drivers": [("FirstName","text",False),("LastName","text",False),("LicenseType","license",False),("ExperienceYears","int",False),("Phone","text",True),("MentorID","driver",True)],
    "jobs": [("TruckID","truck",False),("DriverID","driver",False),("CargoID","cargo",False),("RouteID","route",False),("StartDate","datetime",True),("Status","status",False),("EndDate","datetime",True),("CustomerID","customer",True),("RevenueEUR","decimal",True)],
    "brands": [("BrandName","text",False),("Country","text",True)],
    "garages": [("City","text",False),("Capacity","int",False)],
    "routes": [("DepartureCity","text",False),("ArrivalCity","text",False),("DistanceKm","int",False),("EstimatedHours","decimal",False),("SpecialistDriverID","driver",True)],
    "cargos": [("CargoName","text",False),("WeightKg","int",False),("ValueEUR","decimal",False),("DefaultRouteID","route",True)],
    "customers": [("CompanyName","text",False),("ContactPerson","text",True),("Phone","text",True),("Address","text",True)],
}


def validate_record(table: str, values: Mapping[str, Any], fields: Mapping[str, list[tuple[str, str, bool]]] = FIELDS) -> list[str]:
    """Return actionable validation messages for a record; an empty list is valid."""
    if table not in fields:
        return ["Unsupported record type."]

    problems: list[str] = []
    for name, kind, nullable in fields[table]:
        value = values.get(name)
        if not nullable and kind == "text" and (value is None or not str(value).strip()):
            problems.append(f"{name} is required.")
        elif kind in ("int", "decimal") and value is not None:
            try:
                number = float(value)
            except (TypeError, ValueError):
                problems.append(f"{name} must be a number.")
                continue
            if number < 0:
                problems.append(f"{name} cannot be negative.")
            elif kind == "int" and not number.is_integer():
                problems.append(f"{name} must be a whole number.")

    if table == "jobs":
        start, end = values.get("StartDate"), values.get("EndDate")
        if start is not None and end is not None and end < start:
            problems.append("EndDate must be the same as or later than StartDate.")

    return problems
