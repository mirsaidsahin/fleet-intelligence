"""Builds the shared application context once per Streamlit server process."""
from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from services.health_service import HealthService
from services.schema_verifier import SchemaVerifier
from utils.config import ConfigError, Settings, load_settings
from utils.db import Database
from utils.logging_setup import configure_logging


@dataclass(frozen=True)
class AppContext:
    settings: Settings | None
    database: Database | None
    health: HealthService | None
    config_problems: tuple[str, ...] = ()


@st.cache_resource(show_spinner=False)
def get_app_context() -> AppContext:
    try:
        settings = load_settings()
    except ConfigError as exc:
        return AppContext(None, None, None, exc.problems)
    configure_logging(settings.log_level, settings.secrets())
    database = Database.from_settings(settings)
    health = HealthService(database, SchemaVerifier(database.engine))
    return AppContext(settings, database, health)
