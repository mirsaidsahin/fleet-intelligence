from models.schema_spec import EXPECTED_SCHEMA
from services.schema_verifier import compare_schema


class FakeInspector:
    """Mimics the parts of the SQLAlchemy Inspector the verifier uses."""

    def __init__(self, tables=None, views=None, columns=None, fks=None):
        self.tables = tables if tables is not None else list(EXPECTED_SCHEMA.tables)
        self.views = views if views is not None else list(EXPECTED_SCHEMA.views)
        self.columns = columns or {}
        self.fks = fks if fks is not None else {}

    def get_table_names(self):
        return self.tables

    def get_view_names(self):
        return self.views

    def get_columns(self, table):
        cols = self.columns.get(table, EXPECTED_SCHEMA.tables.get(table.lower(), ()))
        return [{"name": c} for c in cols]

    def get_foreign_keys(self, table):
        if table in self.fks:
            return self.fks[table]
        return [
            {"constrained_columns": [fk.column], "referred_table": fk.ref_table, "referred_columns": [fk.ref_column]}
            for fk in EXPECTED_SCHEMA.foreign_keys
            if fk.table == table
        ]


def test_matching_schema_passes():
    result = compare_schema(FakeInspector())
    assert result.ok
    assert (result.tables_found, result.views_found, result.foreign_keys_found) == (8, 1, 11)


def test_missing_table_view_and_column_are_reported():
    insp = FakeInspector(
        tables=[t for t in EXPECTED_SCHEMA.tables if t != "garages"],
        views=[],
        columns={"trucks": ("TruckID", "Model")},
    )
    result = compare_schema(insp)
    assert not result.ok
    assert result.missing_tables == ("garages",)
    assert result.missing_views == ("vw_activejobsreport",)
    assert dict(result.missing_columns)["trucks"][0] == "BrandID"
    assert any("garages" in p for p in result.problems())


def test_missing_foreign_key_is_reported():
    insp = FakeInspector(fks={"jobs": []})
    result = compare_schema(insp)
    assert "jobs.TruckID -> trucks.TruckID" in result.missing_foreign_keys
    assert result.foreign_keys_found == 6  # 11 expected minus the 5 on jobs


def test_names_compare_case_insensitively_and_extra_columns_are_tolerated():
    insp = FakeInspector(tables=[t.upper() for t in EXPECTED_SCHEMA.tables])
    insp.columns = {t.upper(): tuple(c.lower() for c in cols) + ("Extra",) for t, cols in EXPECTED_SCHEMA.tables.items()}
    insp.fks = {
        t.upper(): [
            {"constrained_columns": [fk.column.lower()], "referred_table": fk.ref_table.upper(), "referred_columns": [fk.ref_column.lower()]}
            for fk in EXPECTED_SCHEMA.foreign_keys
            if fk.table == t
        ]
        for t in EXPECTED_SCHEMA.tables
    }
    assert compare_schema(insp).ok
