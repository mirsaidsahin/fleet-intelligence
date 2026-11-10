from utils.db_errors import describe_db_error, is_connection_error


class FakeDriverError(Exception):
    pass


class OperationalError(Exception):  # same class name SQLAlchemy uses
    def __init__(self, orig):
        super().__init__("wrapped")
        self.orig = orig


def test_known_mysql_codes_map_to_safe_messages():
    assert "Authentication failed" in describe_db_error(OperationalError(FakeDriverError(1045, "Access denied for user 'x'@'h'")))
    assert "does not exist" in describe_db_error(OperationalError(FakeDriverError(1049, "Unknown database")))
    assert "Cannot reach" in describe_db_error(OperationalError(FakeDriverError(2003, "Can't connect")))


def test_raw_driver_text_is_never_returned():
    msg = describe_db_error(OperationalError(FakeDriverError(1045, "Access denied for user 'root'@'10.0.0.5'")))
    assert "root" not in msg and "10.0.0.5" not in msg


def test_missing_cryptography_gets_a_helpful_message():
    msg = describe_db_error(RuntimeError("'cryptography' package is required for sha256_password"))
    assert "pip install cryptography" in msg


def test_connection_error_detection_and_fallback():
    assert is_connection_error(OperationalError(FakeDriverError(2013, "lost")))
    assert not is_connection_error(ValueError("x"))
    assert "Unexpected database error" in describe_db_error(ValueError("x"))
