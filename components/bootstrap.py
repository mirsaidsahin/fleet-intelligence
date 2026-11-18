"""Builds the shared application context once per Streamlit server process."""
from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from utils.config import ConfigError, Settings, load_settings
from utils.db import Database
from utils.logging_setup import configure_logging


@dataclass(frozen=True)
class AppContext:
    """Shared runtime dependencies and configuration diagnostics for a session."""

    settings: Settings | None
    database: Database | None
    config_problems: tuple[str, ...] = ()


@st.cache_resource(show_spinner=False)
def get_app_context() -> AppContext:
    """Load settings once, then build the reusable database service."""
    try:
        # Keep configuration errors as page-readable messages instead of crashing startup.
        settings = load_settings()
    except ConfigError as exc:
        return AppContext(None, None, exc.problems)
    # Register secret redaction before any connection-related details are logged.
    configure_logging(settings.log_level, settings.secrets())
    # Engine creation is lazy; no database connection is opened at this point.
    database = Database.from_settings(settings)
    return AppContext(settings, database)
