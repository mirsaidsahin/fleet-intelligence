"""SQLite integration checks for real SQL execution without a MySQL server."""
from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, event, text

from repositories.fleet import FleetRepository


class SQLiteDatabase:
    def __init__(self, engine):
        self.engine = engine

    def fetch_one(self, sql, params=None):
        with self.engine.connect() as connection:
            row = connection.execute(text(sql), params or {}).mappings().first()
            return dict(row) if row else None

    def fetch_all(self, sql, params=None):
        with self.engine.connect() as connection:
            return [dict(row) for row in connection.execute(text(sql), params or {}).mappings()]

    @contextmanager
    def transaction(self):
        with self.engine.begin() as connection:
            yield connection


@pytest.fixture
def sqlite_repo():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE brands (BrandID INTEGER PRIMARY KEY AUTOINCREMENT, BrandName TEXT NOT NULL, Country TEXT)"))
        connection.execute(text("CREATE TABLE trucks (TruckID INTEGER PRIMARY KEY AUTOINCREMENT, BrandID INTEGER, Model TEXT, FOREIGN KEY (BrandID) REFERENCES brands(BrandID))"))
        connection.execute(text("CREATE TABLE routes (RouteID INTEGER PRIMARY KEY, EstimatedHours FLOAT NOT NULL)"))
        connection.execute(text("CREATE TABLE jobs (JobID INTEGER PRIMARY KEY, TruckID INTEGER, DriverID INTEGER, RouteID INTEGER, StartDate DATETIME, EndDate DATETIME, Status TEXT, FOREIGN KEY (RouteID) REFERENCES routes(RouteID))"))
    yield FleetRepository(SQLiteDatabase(engine))
    engine.dispose()


def test_sqlite_create_update_and_delete_round_trip(sqlite_repo):
    sqlite_repo.save("brands", {"BrandName": "Volvo", "Country": "Sweden"})
    created = sqlite_repo.db.fetch_one("SELECT * FROM brands WHERE BrandName=:name", {"name": "Volvo"})
    assert created == {"BrandID": 1, "BrandName": "Volvo", "Country": "Sweden"}

    sqlite_repo.save("brands", {"BrandName": "Volvo Trucks"}, record_id=1)
    updated = sqlite_repo.db.fetch_one("SELECT BrandName FROM brands WHERE BrandID=:id", {"id": 1})
    assert updated["BrandName"] == "Volvo Trucks"

    sqlite_repo.delete("brands", 1)
    assert sqlite_repo.db.fetch_one("SELECT BrandID FROM brands WHERE BrandID=:id", {"id": 1}) is None


def test_linked_record_counts_report_references_before_delete(sqlite_repo):
    sqlite_repo.save("brands", {"BrandName": "Volvo"})
    sqlite_repo.save("trucks", {"BrandID": 1, "Model": "FH"})

    assert sqlite_repo.linked_record_counts("brands", 1) == {"trucks": 1}


def test_delete_keeps_foreign_key_rejection_as_final_safety(sqlite_repo):
    sqlite_repo.save("brands", {"BrandName": "Volvo"})
    sqlite_repo.save("trucks", {"BrandID": 1, "Model": "FH"})

    assert sqlite_repo.linked_record_counts("brands", 1)["trucks"] == 1
    # UI disables the action; the real DB constraint still protects direct writes.
    with pytest.raises(Exception):
        sqlite_repo.delete("brands", 1)


def test_assignment_conflict_query_finds_overlapping_job_and_excludes_current(sqlite_repo):
    from datetime import datetime

    with sqlite_repo.db.engine.begin() as connection:
        connection.execute(text("INSERT INTO routes VALUES (1, 2.0)"))
        connection.execute(text("INSERT INTO jobs VALUES (9, 4, 7, 1, :start, NULL, 'Pending')"), {"start": "2026-11-12 13:00:00"})
    values = {"TruckID": 4, "DriverID": 8, "RouteID": 1,
              "StartDate": datetime(2026, 11, 12, 12), "Status": "Pending"}

    found = sqlite_repo.assignment_conflicts(values)
    assert [job["JobID"] for job in found] == [9]
    assert sqlite_repo.assignment_conflicts(values, exclude_job_id=9) == []
