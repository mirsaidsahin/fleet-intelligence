"""Translate database exceptions into short, safe messages for the UI.

Raw driver messages can contain hosts, users or SQL, so they go to the log only.
Classes are matched by name so this module has no hard dependency on a driver.
"""
from __future__ import annotations

_BY_CODE = {
    1044: "The database user has no access to this database. Check the grants for DB_USER.",
    1045: "Authentication failed. Check DB_USER and DB_PASSWORD.",
    1049: "The configured database does not exist on the server. Check DB_NAME.",
    2002: "Cannot reach the MySQL server. Check that the service is running and that DB_HOST and DB_PORT are correct.",
    2003: "Cannot reach the MySQL server. Check that the service is running and that DB_HOST and DB_PORT are correct.",
    2005: "The MySQL host name is unknown. Check DB_HOST.",
    2006: "The MySQL server closed the connection.",
    2013: "The connection to MySQL was lost during a query.",
    1062: "A record with that unique value already exists. Check the truck plate number.",
    1451: "This record is linked to other records and cannot be deleted yet.",
    1452: "A linked record no longer exists. Refresh the page and check the selected relationships.",
}
_CONNECTION_CLASSES = {"OperationalError", "InterfaceError"}


def mysql_error_code(exc: BaseException) -> int | None:
    orig = getattr(exc, "orig", exc)
    args = getattr(orig, "args", ())
    if args and isinstance(args[0], int):
        return args[0]
    return None


def describe_db_error(exc: BaseException) -> str:
    code = mysql_error_code(exc)
    if code in _BY_CODE:
        return _BY_CODE[code]
    if "cryptography" in str(exc).lower():
        return "The 'cryptography' package is missing. MySQL 8 sign-in needs it: pip install cryptography."
    names = {cls.__name__ for cls in type(exc).__mro__}
    if names & _CONNECTION_CLASSES:
        return "The database is unreachable or refused the connection. See logs/app.log for details."
    return "Unexpected database error. See logs/app.log for details."


def is_connection_error(exc: BaseException) -> bool:
    return bool({cls.__name__ for cls in type(exc).__mro__} & _CONNECTION_CLASSES)
