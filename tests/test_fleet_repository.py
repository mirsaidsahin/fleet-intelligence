from contextlib import contextmanager

import pytest

from repositories.fleet import FleetRepository


class FakeConnection:
    def __init__(self, executed):
        self.executed = executed

    def execute(self, statement, params):
        self.executed.append((str(statement), params))


class FakeDatabase:
    def __init__(self):
        self.executed = []

    @contextmanager
    def transaction(self):
        yield FakeConnection(self.executed)


def test_create_uses_allowlisted_table_and_bound_parameters():
    db = FakeDatabase()
    FleetRepository(db).save("brands", {"BrandName": "Example", "Country": "Finland"})
    sql, params = db.executed[0]
    assert sql == "INSERT INTO brands (BrandName, Country) VALUES (:BrandName, :Country)"
    assert params == {"BrandName": "Example", "Country": "Finland"}


def test_update_and_delete_bind_record_id():
    db = FakeDatabase()
    repo = FleetRepository(db)
    repo.save("garages", {"City": "Tampere", "Capacity": 12}, record_id=4)
    repo.delete("garages", 4)
    assert db.executed[0][0] == "UPDATE garages SET City=:City, Capacity=:Capacity WHERE GarageID=:record_id"
    assert db.executed[0][1] == {"City": "Tampere", "Capacity": 12, "record_id": 4}
    assert db.executed[1] == ("DELETE FROM garages WHERE GarageID=:record_id", {"record_id": 4})


@pytest.mark.parametrize(
    ("table", "values"),
    [
        ("brands; DROP TABLE jobs", {"BrandName": "x"}),
        ("brands", {"BrandName); DROP TABLE jobs; --": "x"}),
        ("brands", {"BrandID": 4}),
    ],
)
def test_rejects_untrusted_table_or_columns_before_execution(table, values):
    db = FakeDatabase()
    repo = FleetRepository(db)
    with pytest.raises(ValueError):
        repo.save(table, values)
    assert db.executed == []


def test_empty_write_is_rejected():
    db = FakeDatabase()
    with pytest.raises(ValueError):
        FleetRepository(db).save("brands", {})
    assert db.executed == []


@pytest.mark.parametrize("table,primary_key,column,value", [
    ("trucks", "TruckID", "Model", "FH"),
    ("drivers", "DriverID", "FirstName", "Ada"),
    ("jobs", "JobID", "Status", "Pending"),
    ("brands", "BrandID", "BrandName", "Volvo"),
    ("garages", "GarageID", "City", "Turku"),
    ("routes", "RouteID", "DepartureCity", "Turku"),
    ("cargos", "CargoID", "CargoName", "Parts"),
    ("customers", "CustomerID", "CompanyName", "Example Ltd"),
])
def test_create_update_and_delete_are_parameterized_for_every_entity(table, primary_key, column, value):
    db = FakeDatabase()
    repo = FleetRepository(db)

    repo.save(table, {column: value})
    repo.save(table, {column: value}, record_id=17)
    repo.delete(table, 17)

    assert db.executed == [
        (f"INSERT INTO {table} ({column}) VALUES (:{column})", {column: value}),
        (f"UPDATE {table} SET {column}=:{column} WHERE {primary_key}=:record_id", {column: value, "record_id": 17}),
        (f"DELETE FROM {table} WHERE {primary_key}=:record_id", {"record_id": 17}),
    ]


@pytest.mark.parametrize("operation", ["save", "delete"])
def test_rejects_unsupported_entity_before_opening_transaction(operation):
    db = FakeDatabase()
    repo = FleetRepository(db)

    with pytest.raises(ValueError, match="Unsupported table"):
        if operation == "save":
            repo.save("unknown", {"Name": "x"})
        else:
            repo.delete("unknown", 1)

    assert db.executed == []
