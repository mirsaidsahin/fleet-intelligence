"""Parameterized, allow-listed SQL access for the fleet domain."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


class FleetRepository:
    TABLES = {
        "trucks": ("TruckID", "BrandID", "Model", "ProductionYear", "RequiredLicense", "PlateNumber", "Mileage", "GarageID", "AssignedDriverID"),
        "drivers": ("DriverID", "FirstName", "LastName", "LicenseType", "ExperienceYears", "Phone", "MentorID"),
        "jobs": ("JobID", "TruckID", "DriverID", "CargoID", "RouteID", "StartDate", "Status", "EndDate", "CustomerID", "RevenueEUR"),
        "brands": ("BrandID", "BrandName", "Country"),
        "garages": ("GarageID", "City", "Capacity"),
        "routes": ("RouteID", "DepartureCity", "ArrivalCity", "DistanceKm", "EstimatedHours", "SpecialistDriverID"),
        "cargos": ("CargoID", "CargoName", "WeightKg", "ValueEUR", "DefaultRouteID"),
        "customers": ("CustomerID", "CompanyName", "ContactPerson", "Phone", "Address"),
    }

    def __init__(self, database: Any) -> None:
        self.db = database

    def rows(self, table: str, limit: int = 500) -> list[dict[str, Any]]:
        self._table(table)
        return self.db.fetch_all(f"SELECT * FROM {table} ORDER BY {self.TABLES[table][0]} DESC LIMIT :limit", {"limit": limit})

    def options(self, table: str, key: str, label: str) -> list[dict[str, Any]]:
        self._table(table)
        cols = self.TABLES[table]
        if key not in cols or label not in cols:
            raise ValueError("Invalid option fields")
        return self.db.fetch_all(f"SELECT {key} AS id, {label} AS label FROM {table} ORDER BY {label}")

    def save(self, table: str, values: Mapping[str, Any], record_id: int | None = None) -> None:
        self._table(table)
        columns = set(self.TABLES[table][1:])
        if not values or set(values) - columns:
            raise ValueError("Invalid fields for this record")
        if record_id is None:
            names = list(values)
            sql = f"INSERT INTO {table} ({', '.join(names)}) VALUES ({', '.join(':'+n for n in names)})"
        else:
            names = list(values)
            sql = f"UPDATE {table} SET {', '.join(n + '=:'+n for n in names)} WHERE {self.TABLES[table][0]}=:record_id"
            values = {**values, "record_id": record_id}
        from sqlalchemy import text
        with self.db.transaction() as conn:
            conn.execute(text(sql), dict(values))

    def delete(self, table: str, record_id: int) -> None:
        self._table(table)
        from sqlalchemy import text
        with self.db.transaction() as conn:
            conn.execute(text(f"DELETE FROM {table} WHERE {self.TABLES[table][0]}=:record_id"), {"record_id": record_id})

    def assignment_conflicts(self, values: Mapping[str, Any], exclude_job_id: int | None = None) -> list[dict[str, Any]]:
        """Find active jobs overlapping the selected truck or driver assignment."""
        if values.get("Status") not in ("Pending", "In Transit"):
            return []
        route_id = values.get("RouteID")
        route = self.db.fetch_one("SELECT EstimatedHours FROM routes WHERE RouteID=:route_id", {"route_id": route_id})
        if route is None:
            return []  # Referential validation/MySQL will report a missing route on save.
        rows = self.db.fetch_all("""SELECT j.JobID, j.Status, j.StartDate, j.EndDate,
            j.TruckID, j.DriverID, r.EstimatedHours
            FROM jobs j JOIN routes r ON r.RouteID=j.RouteID
            WHERE j.Status IN ('Pending','In Transit')
              AND (j.TruckID=:truck_id OR j.DriverID=:driver_id)
              AND (:exclude_id IS NULL OR j.JobID<>:exclude_id)""",
            {"truck_id": values.get("TruckID"), "driver_id": values.get("DriverID"), "exclude_id": exclude_job_id})
        from services.workflow import find_assignment_conflicts
        return find_assignment_conflicts(values, rows, float(route["EstimatedHours"]))

    def linked_record_counts(self, table: str, record_id: int) -> dict[str, int]:
        """Count rows that reference a record before delete; FK rules remain authoritative."""
        references = {
            "trucks": {"jobs": ("TruckID",)},
            "drivers": {"trucks": ("AssignedDriverID",), "jobs": ("DriverID",), "routes": ("SpecialistDriverID",), "drivers": ("MentorID",)},
            "jobs": {},
            "brands": {"trucks": ("BrandID",)},
            "garages": {"trucks": ("GarageID",)},
            "routes": {"jobs": ("RouteID",), "cargos": ("DefaultRouteID",)},
            "cargos": {"jobs": ("CargoID",)},
            "customers": {"jobs": ("CustomerID",)},
        }
        self._table(table)
        from sqlalchemy import text
        counts: dict[str, int] = {}
        for child_table, columns in references[table].items():
            predicates = " OR ".join(f"{column}=:record_id" for column in columns)
            query = text(f"SELECT COUNT(*) AS total FROM {child_table} WHERE {predicates}")
            row = self.db.fetch_one(str(query), {"record_id": record_id})
            counts[child_table] = int((row or {}).get("total", 0))
        return counts

    @classmethod
    def _table(cls, table: str) -> None:
        if table not in cls.TABLES:
            raise ValueError("Unsupported table")


class DashboardRepository:
    def __init__(self, database: Any) -> None:
        self.db = database

    def summary(self) -> dict[str, Any]:
        return self.db.fetch_one("""SELECT
            (SELECT COUNT(*) FROM trucks) AS trucks,
            (SELECT COUNT(*) FROM drivers) AS drivers,
            (SELECT COUNT(*) FROM jobs WHERE Status IN ('Pending','In Transit')) AS open_jobs,
            (SELECT COUNT(*) FROM jobs WHERE Status='In Transit') AS in_transit,
            (SELECT COALESCE(SUM(RevenueEUR),0) FROM jobs WHERE Status='Completed') AS completed_revenue,
            (SELECT COUNT(*) FROM jobs WHERE Status='Pending' AND StartDate < :now) AS overdue""", {"now": datetime.now()}) or {}

    def jobs_by_status(self) -> list[dict[str, Any]]:
        return self.db.fetch_all("SELECT Status AS status, COUNT(*) AS total FROM jobs GROUP BY Status ORDER BY total DESC")

    def monthly_revenue(self) -> list[dict[str, Any]]:
        return self.db.fetch_all("SELECT DATE_FORMAT(StartDate, '%Y-%m') AS month, SUM(RevenueEUR) AS revenue FROM jobs WHERE Status='Completed' AND StartDate IS NOT NULL GROUP BY month ORDER BY month")

    def recent_jobs(self, limit: int = 10) -> list[dict[str, Any]]:
        return self.db.fetch_all("""SELECT j.JobID, j.Status, j.StartDate, j.RevenueEUR, c.CompanyName,
            CONCAT(d.FirstName,' ',d.LastName) AS Driver, CONCAT(r.DepartureCity,' → ',r.ArrivalCity) AS Route
            FROM jobs j LEFT JOIN customers c ON c.CustomerID=j.CustomerID
            JOIN drivers d ON d.DriverID=j.DriverID JOIN routes r ON r.RouteID=j.RouteID
            ORDER BY j.StartDate DESC, j.JobID DESC LIMIT :limit""", {"limit": limit})

    def dispatch_board(self, limit: int = 30) -> list[dict[str, Any]]:
        """Open work with the real truck, driver, customer and route assignment."""
        return self.db.fetch_all("""SELECT j.JobID, j.Status, j.StartDate,
            CONCAT(b.BrandName, ' ', t.Model) AS Truck, t.PlateNumber,
            CONCAT(d.FirstName, ' ', d.LastName) AS Driver,
            CONCAT(r.DepartureCity, ' → ', r.ArrivalCity) AS Route,
            r.DistanceKm, c.CargoName, cu.CompanyName AS Customer
            FROM jobs j JOIN trucks t ON t.TruckID=j.TruckID
            LEFT JOIN brands b ON b.BrandID=t.BrandID
            JOIN drivers d ON d.DriverID=j.DriverID
            JOIN routes r ON r.RouteID=j.RouteID
            JOIN cargos c ON c.CargoID=j.CargoID
            LEFT JOIN customers cu ON cu.CustomerID=j.CustomerID
            WHERE j.Status IN ('In Transit','Pending')
            ORDER BY CASE j.Status WHEN 'In Transit' THEN 0 ELSE 1 END,
                     j.StartDate ASC, j.JobID LIMIT :limit""", {"limit": limit})

    def active_truck_positions(self, limit: int = 200) -> list[dict[str, Any]]:
        """Return in-transit assignments and route timing for estimated map positions."""
        return self.db.fetch_all("""SELECT j.JobID, j.TruckID, j.DriverID, j.Status, j.StartDate,
            t.BrandID,
            CONCAT(b.BrandName, ' ', t.Model) AS Truck, t.PlateNumber,
            CONCAT(d.FirstName, ' ', d.LastName) AS Driver,
            r.RouteID, r.DepartureCity, r.ArrivalCity, r.DistanceKm, r.EstimatedHours,
            c.CargoName, cu.CompanyName AS Customer
            FROM jobs j JOIN trucks t ON t.TruckID=j.TruckID
            LEFT JOIN brands b ON b.BrandID=t.BrandID
            JOIN drivers d ON d.DriverID=j.DriverID
            JOIN routes r ON r.RouteID=j.RouteID
            LEFT JOIN cargos c ON c.CargoID=j.CargoID
            LEFT JOIN customers cu ON cu.CustomerID=j.CustomerID
            WHERE j.Status='In Transit'
            ORDER BY j.StartDate, j.JobID LIMIT :limit""", {"limit": limit})

    def route_network(self) -> list[dict[str, Any]]:
        """Route nodes and workload counts from the existing MySQL records."""
        return self.db.fetch_all("""SELECT r.RouteID, r.DepartureCity, r.ArrivalCity,
            r.DistanceKm, r.EstimatedHours,
            SUM(CASE WHEN j.Status='In Transit' THEN 1 ELSE 0 END) AS in_transit,
            SUM(CASE WHEN j.Status='Pending' THEN 1 ELSE 0 END) AS pending
            FROM routes r LEFT JOIN jobs j ON j.RouteID=r.RouteID
                AND j.Status IN ('In Transit','Pending')
            GROUP BY r.RouteID, r.DepartureCity, r.ArrivalCity,
                     r.DistanceKm, r.EstimatedHours
            ORDER BY r.RouteID""")

    def operational_alerts(self, limit: int = 20) -> list[dict[str, Any]]:
        """Explainable alerts calculated from pending starts and estimated durations."""
        return self.db.fetch_all("""SELECT 'Pending past start' AS Alert,
            'Review dispatch' AS Action, j.JobID,
            CONCAT(r.DepartureCity, ' → ', r.ArrivalCity) AS Route,
            CONCAT(d.FirstName, ' ', d.LastName) AS Driver, j.StartDate
            FROM jobs j JOIN routes r ON r.RouteID=j.RouteID
            JOIN drivers d ON d.DriverID=j.DriverID
            WHERE j.Status='Pending' AND j.StartDate < NOW()
            UNION ALL
            SELECT 'Transit exceeds estimate' AS Alert,
            'Check vehicle status' AS Action, j.JobID,
            CONCAT(r.DepartureCity, ' → ', r.ArrivalCity) AS Route,
            CONCAT(d.FirstName, ' ', d.LastName) AS Driver, j.StartDate
            FROM jobs j JOIN routes r ON r.RouteID=j.RouteID
            JOIN drivers d ON d.DriverID=j.DriverID
            WHERE j.Status='In Transit'
              AND j.StartDate < DATE_SUB(NOW(), INTERVAL r.EstimatedHours HOUR)
            ORDER BY StartDate LIMIT :limit""", {"limit": limit})

    def driver_scoreboard(self) -> list[dict[str, Any]]:
        """Completed-work performance based only on recorded job and route data."""
        return self.db.fetch_all("""SELECT d.DriverID,
            CONCAT(d.FirstName, ' ', d.LastName) AS Driver,
            d.ExperienceYears,
            SUM(CASE WHEN j.Status='Completed' THEN 1 ELSE 0 END) AS CompletedJobs,
            COALESCE(SUM(CASE WHEN j.Status='Completed' THEN j.RevenueEUR ELSE 0 END),0) AS RevenueEUR,
            COALESCE(SUM(CASE WHEN j.Status='Completed' THEN r.DistanceKm ELSE 0 END),0) AS DistanceKm,
            SUM(CASE WHEN j.Status='Completed' AND j.StartDate IS NOT NULL
                AND j.EndDate IS NOT NULL
                AND j.EndDate <= DATE_ADD(j.StartDate, INTERVAL r.EstimatedHours HOUR)
                THEN 1 ELSE 0 END) AS OnTimeJobs
            FROM drivers d LEFT JOIN jobs j ON j.DriverID=d.DriverID
            LEFT JOIN routes r ON r.RouteID=j.RouteID
            GROUP BY d.DriverID, d.FirstName, d.LastName, d.ExperienceYears
            ORDER BY CompletedJobs DESC, RevenueEUR DESC, Driver""")

    def truck_statuses(self) -> list[dict[str, Any]]:
        from models.status import OpenJob
        from services.fleet_status import classify

        rows = self.db.fetch_all("""SELECT t.TruckID, t.PlateNumber, b.BrandName, t.Model,
            j.JobID, j.Status, j.StartDate, r.EstimatedHours
            FROM trucks t LEFT JOIN brands b ON b.BrandID=t.BrandID
            LEFT JOIN jobs j ON j.TruckID=t.TruckID AND j.Status IN ('Pending','In Transit')
            LEFT JOIN routes r ON r.RouteID=j.RouteID ORDER BY t.TruckID,j.JobID""")
        grouped: dict[int, dict[str, Any]] = {}
        jobs: dict[int, list[OpenJob]] = {}
        for row in rows:
            truck_id = int(row["TruckID"])
            grouped.setdefault(truck_id, {k: row[k] for k in ("TruckID", "PlateNumber", "BrandName", "Model")})
            if row["JobID"] is not None:
                jobs.setdefault(truck_id, []).append(OpenJob(int(row["JobID"]), row["Status"], row["StartDate"], float(row["EstimatedHours"] or 0)))
        now = datetime.now()
        return [{**truck, "Status": classify(jobs.get(truck_id, []), now).value} for truck_id, truck in grouped.items()]

