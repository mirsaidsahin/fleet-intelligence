from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from components import status_bar
from utils.db import ConnectionStatus

T0 = datetime(2026, 10, 29, 12, 0, 0).astimezone()


class FakeDb:
    def __init__(self, *statuses):
        self.statuses = list(statuses)

    def ping(self):
        return self.statuses.pop(0)


def up(t):
    return ConnectionStatus(True, t, 3.0, "8.0.46", "omnilogistics")


def down(t):
    return ConnectionStatus(False, t, error="Cannot reach the MySQL server.")


@pytest.fixture
def state(monkeypatch):
    session = {}
    monkeypatch.setattr(status_bar.st, "session_state", session)
    return session


def test_connected_status_records_success_time(state):
    status = status_bar.current_status(SimpleNamespace(database=FakeDb(up(T0))))
    assert status.connected
    assert status_bar.last_success_at() == T0


def test_disconnected_status_has_no_success_time(state):
    status = status_bar.current_status(SimpleNamespace(database=FakeDb(down(T0))))
    assert not status.connected
    assert status_bar.last_success_at() is None


def test_failure_keeps_previous_success_time(state):
    ctx = SimpleNamespace(database=FakeDb(up(T0), down(T0 + timedelta(minutes=5))))
    status_bar.current_status(ctx)
    state[status_bar.FORCE_KEY] = True
    second = status_bar.current_status(ctx)
    assert not second.connected
    assert status_bar.last_success_at() == T0
