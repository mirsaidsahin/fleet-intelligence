"""Application settings loaded from environment variables and an optional .env file.

Real environment variables win over .env values. Error messages name variables
only and never echo values, so a bad password cannot leak through a ConfigError.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"

REQUIRED_VARS = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
OPTIONAL_VARS = (
    "DB_PORT",
    "DB_POOL_SIZE",
    "DB_CONNECT_TIMEOUT",
    "STATUS_TTL_SECONDS",
    "CACHE_TTL_SECONDS",
    "LOG_LEVEL",
)
ALL_VARS = REQUIRED_VARS + OPTIONAL_VARS
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")
_DEFAULT = object()  # sentinel: resolve DEFAULT_ENV_FILE at call time so tests can override it


class ConfigError(Exception):
    """Configuration is missing or invalid. Carries variable names, never values."""

    def __init__(self, problems: list[str]) -> None:
        self.problems: tuple[str, ...] = tuple(problems)
        super().__init__("; ".join(problems))


@dataclass(frozen=True)
class Settings:
    db_host: str
    db_name: str
    db_user: str
    db_password: str = field(repr=False)
    db_port: int = 3306
    pool_size: int = 5
    connect_timeout: int = 5
    status_ttl_seconds: int = 60
    cache_ttl_seconds: int = 120
    log_level: str = "INFO"

    def sqlalchemy_url(self):
        """Build the connection URL. The password is never formatted into a string here."""
        from sqlalchemy.engine import URL  # imported lazily so config stays light

        return URL.create(
            "mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )

    def safe_dsn(self) -> str:
        """Connection string with the password masked, safe for logs and the UI."""
        return f"mysql+pymysql://{self.db_user}:***@{self.db_host}:{self.db_port}/{self.db_name}"

    def secrets(self) -> tuple[str, ...]:
        """Return non-empty values that logging must redact."""
        return (self.db_password,) if self.db_password else ()


def _read_int(env: Mapping[str, str], name: str, default: int, low: int, high: int, problems: list[str]) -> int:
    """Parse one bounded integer setting and record invalid input by name."""
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        value = None
    if value is None or not low <= value <= high:
        problems.append(f"{name} must be an integer between {low} and {high}")
        return default
    return value


def settings_from_mapping(env: Mapping[str, str]) -> Settings:
    """Validate a mapping of variables and build Settings, or raise ConfigError."""
    problems: list[str] = []

    # Required variables are checked without copying secret values into errors.
    for name in REQUIRED_VARS:
        value = env.get(name)
        if value is None:
            problems.append(f"{name} is not set")
        elif name != "DB_PASSWORD" and value.strip() == "":
            problems.append(f"{name} is empty")

    log_level = (env.get("LOG_LEVEL") or "INFO").strip().upper()
    # Normalize level names once, then fall back safely if the value is unknown.
    if log_level not in LOG_LEVELS:
        problems.append(f"LOG_LEVEL must be one of {', '.join(LOG_LEVELS)}")
        log_level = "INFO"

    port = _read_int(env, "DB_PORT", 3306, 1, 65535, problems)
    pool_size = _read_int(env, "DB_POOL_SIZE", 5, 1, 20, problems)
    connect_timeout = _read_int(env, "DB_CONNECT_TIMEOUT", 5, 1, 60, problems)
    status_ttl = _read_int(env, "STATUS_TTL_SECONDS", 60, 5, 3600, problems)
    cache_ttl = _read_int(env, "CACHE_TTL_SECONDS", 120, 5, 3600, problems)

    if problems:
        raise ConfigError(problems)

    return Settings(
        db_host=env["DB_HOST"].strip(),
        db_name=env["DB_NAME"].strip(),
        db_user=env["DB_USER"].strip(),
        db_password=env["DB_PASSWORD"],
        db_port=port,
        pool_size=pool_size,
        connect_timeout=connect_timeout,
        status_ttl_seconds=status_ttl,
        cache_ttl_seconds=cache_ttl,
        log_level=log_level,
    )


def _merged_env(env_file: Path | None | object, environ: Mapping[str, str] | None) -> dict[str, str]:
    """Return .env values (if the file exists) overlaid by real environment variables.

    .env is read into a dict and never copied into os.environ, so editing the
    file and pressing Refresh in the app picks up the change.
    """
    if env_file is _DEFAULT:
        env_file = DEFAULT_ENV_FILE
    file_values: dict[str, str] = {}
    if env_file is not None and Path(env_file).is_file():
        file_values = {k: v for k, v in dotenv_values(env_file).items() if v is not None}
    real = os.environ if environ is None else environ
    return {**file_values, **real}


def load_settings(env_file: Path | None | object = _DEFAULT, environ: Mapping[str, str] | None = None) -> Settings:
    """Load settings from .env (if present) overlaid by real environment variables."""
    return settings_from_mapping(_merged_env(env_file, environ))


def configuration_report(env_file: Path | None | object = _DEFAULT, environ: Mapping[str, str] | None = None) -> dict[str, bool]:
    """Which variables are set (True/False). Names only; used by the System page."""
    merged = _merged_env(env_file, environ)
    # Expose only whether each known variable is present, never its value.
    return {name: name in merged and (merged[name].strip() != "" or name == "DB_PASSWORD") for name in ALL_VARS}
