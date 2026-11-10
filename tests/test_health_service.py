from datetime import datetime, timedelta

from models.health import ConnectionStatus, SchemaCheckResult
from services.health_service import HealthService

T0 = datetime(2026, 10, 29, 12, 0, 0)
OK_SCHEMA = SchemaCheckResult(8, 8, 1, 1, 11, 11)


class FakeDb:
    def __init__(self, *statuses):
        self.statuses = list(statuses)

    def ping(self):
        return self.statuses.pop(0)


class FakeVerifier:
    def __init__(self):
        self.calls = 0

    def verify(self):
        self.calls += 1
        return OK_SCHEMA


def up(t):
    return ConnectionStatus(True, t, 3.0, "8.0.46", "omnilogistics")


def down(t):
    return ConnectionStatus(False, t, error="Cannot reach the MySQL server.")


def test_connected_report_runs_schema_check():
    verifier = FakeVerifier()
    report = HealthService(FakeDb(up(T0)), verifier).check()
    assert report.connection.connected and report.schema is OK_SCHEMA
    assert report.last_success_at == T0 and verifier.calls == 1


def test_disconnected_report_skips_schema_and_has_no_success_time():
    verifier = FakeVerifier()
    report = HealthService(FakeDb(down(T0)), verifier).check()
    assert not report.connection.connected and report.schema is None
    assert report.last_success_at is None and verifier.calls == 0


def test_failure_keeps_previous_success_time_and_schema():
    verifier = FakeVerifier()
    service = HealthService(FakeDb(up(T0), down(T0 + timedelta(minutes=5))), verifier)
    first = service.check()
    second = service.check(first, verify_schema=False)
    assert second.last_success_at == T0
    assert second.schema is OK_SCHEMA and verifier.calls == 1


def test_schema_not_rechecked_when_not_requested():
    verifier = FakeVerifier()
    service = HealthService(FakeDb(up(T0), up(T0 + timedelta(seconds=70))), verifier)
    first = service.check()
    service.check(first, verify_schema=False)
    assert verifier.calls == 1
