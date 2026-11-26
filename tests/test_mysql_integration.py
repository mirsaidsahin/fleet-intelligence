"""MySQL integration test: Python and MySQL working together, on a separate test database.

Opt-in only, so the normal `pytest` run never touches MySQL:
    1. Run database/create_test_database.sql once in MySQL Workbench.
    2. PowerShell: $env:RUN_MYSQL_TESTS = "1"; pytest tests/test_mysql_integration.py -v
"""
import os
import uuid

import pytest
from sqlalchemy import text

from repositories.fleet import FleetRepository
from utils import config
from utils.db import Database

TEST_DB_NAME = "omnilogistics_test"

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_MYSQL_TESTS") != "1", reason="set RUN_MYSQL_TESTS=1 to run MySQL integration tests"
)


@pytest.fixture
def test_db(monkeypatch):
    """Connect to the TEST database using the .env credentials, never the real database."""
    env_file = config.PROJECT_ROOT / ".env"
    if not env_file.is_file():
        pytest.skip("no .env file with database credentials")
    # monkeypatch overrides DB_NAME only for this test; .env itself is not changed.
    monkeypatch.setenv("DB_NAME", TEST_DB_NAME)
    settings = config.load_settings(env_file=env_file)
    assert settings.db_name == TEST_DB_NAME  # safety: refuse to run against the real database

    database = Database.from_settings(settings)
    status = database.ping()
    if not status.connected:
        pytest.skip(f"MySQL test database not reachable: {status.error}")
    yield database
    database.engine.dispose()


def test_created_brand_is_committed_to_mysql(test_db):
    # Arrange: a unique name so the test never collides with other rows.
    name = f"Integration Test {uuid.uuid4().hex[:8]}"
    repo = FleetRepository(test_db)
    try:
        # Act: insert through the same repository method the Streamlit form uses.
        repo.save("brands", {"BrandName": name, "Country": "Finland"})

        # Assert: a new connection sees the row, so the INSERT was committed.
        row = test_db.fetch_one(
            "SELECT BrandName, Country FROM brands WHERE BrandName = :name", {"name": name}
        )
        assert row == {"BrandName": name, "Country": "Finland"}
    finally:
        # Clean up the test row even if an assertion failed.
        with test_db.transaction() as connection:
            connection.execute(text("DELETE FROM brands WHERE BrandName = :name"), {"name": name})

    assert test_db.fetch_one("SELECT BrandID FROM brands WHERE BrandName = :name", {"name": name}) is None
