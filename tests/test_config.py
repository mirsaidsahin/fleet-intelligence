from pathlib import Path

import pytest

from utils.config import ALL_VARS, ConfigError, load_settings, settings_from_mapping

VALID = {"DB_HOST": "127.0.0.1", "DB_NAME": "omnilogistics", "DB_USER": "fleet_app", "DB_PASSWORD": "s3cret-pw"}


def test_valid_settings_use_defaults():
    s = settings_from_mapping(VALID)
    assert (s.db_host, s.db_name, s.db_port, s.pool_size) == ("127.0.0.1", "omnilogistics", 3306, 5)


def test_missing_variables_are_named_without_values():
    with pytest.raises(ConfigError) as err:
        settings_from_mapping({"DB_HOST": "h"})
    text = str(err.value)
    assert "DB_NAME is not set" in text and "DB_USER is not set" in text and "DB_PASSWORD is not set" in text


def test_empty_password_is_allowed_but_empty_user_is_not():
    s = settings_from_mapping({**VALID, "DB_PASSWORD": ""})
    assert s.db_password == ""
    with pytest.raises(ConfigError):
        settings_from_mapping({**VALID, "DB_USER": "  "})


def test_invalid_port_and_log_level_are_reported():
    with pytest.raises(ConfigError) as err:
        settings_from_mapping({**VALID, "DB_PORT": "abc", "LOG_LEVEL": "LOUD"})
    assert "DB_PORT" in str(err.value) and "LOG_LEVEL" in str(err.value)
    with pytest.raises(ConfigError):
        settings_from_mapping({**VALID, "DB_PORT": "70000"})


def test_password_never_appears_in_repr_or_safe_dsn_or_errors():
    s = settings_from_mapping(VALID)
    assert "s3cret-pw" not in repr(s)
    assert "s3cret-pw" not in s.safe_dsn()
    assert s.secrets() == ("s3cret-pw",)
    with pytest.raises(ConfigError) as err:
        settings_from_mapping({**VALID, "DB_PORT": "s3cret-pw"})
    assert "s3cret-pw" not in str(err.value)


def test_real_environment_overrides_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=from-file\nDB_NAME=n\nDB_USER=u\nDB_PASSWORD=p\n")
    s = load_settings(env_file, environ={"DB_HOST": "from-env"})
    assert s.db_host == "from-env" and s.db_name == "n"


def test_env_example_lists_every_variable_with_placeholder_secret():
    text = (Path(__file__).resolve().parent.parent / ".env.example").read_text()
    keys = {line.split("=")[0] for line in text.splitlines() if "=" in line and not line.startswith("#")}
    assert keys == set(ALL_VARS)
    assert "DB_PASSWORD=change_me" in text
