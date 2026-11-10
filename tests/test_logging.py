import logging

from utils.logging_setup import RedactingFormatter


def test_secret_is_redacted_in_message_and_traceback():
    formatter = RedactingFormatter("%(message)s", secrets=["hunter2"])
    try:
        raise RuntimeError("login failed with hunter2")
    except RuntimeError:
        import sys

        record = logging.LogRecord("fleet.db", logging.ERROR, __file__, 1, "password hunter2 rejected", None, sys.exc_info())
    out = formatter.format(record)
    assert "hunter2" not in out and "***" in out
