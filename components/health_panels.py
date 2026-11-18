"""Reusable panels that show connection state."""
from __future__ import annotations

from datetime import datetime
from html import escape

import streamlit as st

from utils.config import Settings
from utils.db import ConnectionStatus

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def kv_card(title: str, rows: list[tuple[str, str, str]]) -> None:
    """Card with label/value rows. Each row is (label, value, css modifier or '')."""
    body = "".join(
        f'<div class="fi-kv"><span>{escape(label)}</span><span class="{cls}">{escape(value)}</span></div>'
        for label, value, cls in rows
    )
    st.markdown(
        f'<div class="fi-card"><div class="fi-card-title">{escape(title)}</div>{body}</div>',
        unsafe_allow_html=True,
    )


def connection_card(
    conn: ConnectionStatus | None, last_success: datetime | None, settings: Settings | None
) -> None:
    """Show connection state, target, latency, and most recent check times."""
    if conn is None:
        kv_card("Database connection", [("State", "Not configured", "fi-warn-text")])
        return
    state = ("Connected", "fi-ok-text") if conn.connected else ("Not reachable", "fi-bad-text")
    rows = [("State", *state)]
    if settings is not None:
        rows.append(("Server", f"{settings.db_host}:{settings.db_port}", ""))
    if conn.connected:
        rows += [
            ("Database", str(conn.database), ""),
            ("MySQL version", str(conn.server_version), ""),
            ("Round trip", f"{conn.latency_ms} ms", ""),
        ]
    else:
        rows.append(("Reason", conn.error or "Unknown", "fi-bad-text"))
    rows.append(("Last checked", conn.checked_at.strftime(TIME_FORMAT), ""))
    rows.append(("Last successful", last_success.strftime(TIME_FORMAT) if last_success else "Never", ""))
    kv_card("Database connection", rows)

