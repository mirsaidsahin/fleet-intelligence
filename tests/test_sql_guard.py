import pytest

from utils.sql_guard import assert_read_only


def test_plain_select_and_with_are_allowed():
    assert_read_only("SELECT * FROM trucks WHERE TruckID = :id")
    assert_read_only("-- note\nSELECT 1;")
    assert_read_only("WITH x AS (SELECT 1) SELECT * FROM x")


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE trucks",
        "DELETE FROM jobs",
        "UPDATE trucks SET Mileage = 0",
        "INSERT INTO brands VALUES (1)",
        "SELECT 1; DROP TABLE trucks",
        "WITH x AS (SELECT 1) DELETE FROM jobs",
        "SELECT 1 # hidden\n; DROP TABLE trucks",
        "",
    ],
)
def test_write_and_multi_statement_sql_is_rejected(sql):
    with pytest.raises(ValueError):
        assert_read_only(sql)
