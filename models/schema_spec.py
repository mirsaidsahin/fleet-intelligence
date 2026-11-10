"""The schema the application expects, taken from the supplied omnilogistics dump.

Only names and relationships are checked. Types and row counts are deliberately
left out so harmless differences do not raise false alarms.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ForeignKeySpec:
    table: str
    column: str
    ref_table: str
    ref_column: str

    def label(self) -> str:
        return f"{self.table}.{self.column} -> {self.ref_table}.{self.ref_column}"


@dataclass(frozen=True)
class SchemaSpec:
    tables: dict[str, tuple[str, ...]]
    views: tuple[str, ...]
    foreign_keys: tuple[ForeignKeySpec, ...]


EXPECTED_SCHEMA = SchemaSpec(
    tables={
        "brands": ("BrandID", "BrandName", "Country"),
        "customers": ("CustomerID", "CompanyName", "ContactPerson", "Phone", "Address"),
        "garages": ("GarageID", "City", "Capacity"),
        "drivers": ("DriverID", "FirstName", "LastName", "LicenseType", "ExperienceYears", "Phone", "MentorID"),
        "routes": ("RouteID", "DepartureCity", "ArrivalCity", "DistanceKm", "EstimatedHours", "SpecialistDriverID"),
        "cargos": ("CargoID", "CargoName", "WeightKg", "ValueEUR", "DefaultRouteID"),
        "trucks": (
            "TruckID", "BrandID", "Model", "ProductionYear", "RequiredLicense",
            "PlateNumber", "Mileage", "GarageID", "AssignedDriverID",
        ),
        "jobs": (
            "JobID", "TruckID", "DriverID", "CargoID", "RouteID", "StartDate",
            "Status", "EndDate", "CustomerID", "RevenueEUR",
        ),
    },
    views=("vw_activejobsreport",),
    foreign_keys=(
        ForeignKeySpec("drivers", "MentorID", "drivers", "DriverID"),
        ForeignKeySpec("routes", "SpecialistDriverID", "drivers", "DriverID"),
        ForeignKeySpec("cargos", "DefaultRouteID", "routes", "RouteID"),
        ForeignKeySpec("trucks", "BrandID", "brands", "BrandID"),
        ForeignKeySpec("trucks", "GarageID", "garages", "GarageID"),
        ForeignKeySpec("trucks", "AssignedDriverID", "drivers", "DriverID"),
        ForeignKeySpec("jobs", "TruckID", "trucks", "TruckID"),
        ForeignKeySpec("jobs", "DriverID", "drivers", "DriverID"),
        ForeignKeySpec("jobs", "CargoID", "cargos", "CargoID"),
        ForeignKeySpec("jobs", "RouteID", "routes", "RouteID"),
        ForeignKeySpec("jobs", "CustomerID", "customers", "CustomerID"),
    ),
)

# Row counts in the dump of 2026-10-29. Informational only: live data may differ.
REFERENCE_ROW_COUNTS = {
    "brands": 11, "customers": 12, "garages": 12, "drivers": 30,
    "routes": 10, "cargos": 30, "trucks": 30, "jobs": 50,
}
