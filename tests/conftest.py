"""Test safety: no test may read the real .env or reach a real MySQL server."""
import pytest

from utils import config

DB_VARS = (*config.ALL_VARS,)


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch):
    for name in DB_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(config, "DEFAULT_ENV_FILE", None)
