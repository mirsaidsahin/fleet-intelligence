"""Top status bar. Everything shown comes from a real check; nothing is labelled live."""
from __future__ import annotations

from datetime import datetime
from html import escape

import streamlit as st

from components.bootstrap import AppContext, get_app_context
from utils.config import STATUS_TTL_SECONDS
from utils.db import ConnectionStatus
from utils.version import APP_NAME

STATE_KEY = "fi_status"
LAST_SUCCESS_KEY = "fi_last_success"
FORCE_KEY = "fi_force_refresh"
TIME_FORMAT = "%d %b %Y · %H:%M"


def _on_refresh(ctx: AppContext) -> None:
    """Mark cached dashboard data stale and reload settings when needed."""
    st.session_state[FORCE_KEY] = True
    st.cache_data.clear()  # read caches added in later phases are dropped here too
    if ctx.settings is None:
        get_app_context.clear()  # re-read .env after the user fixed it


def current_status(ctx: AppContext) -> ConnectionStatus | None:
    """Return the latest status, re-pinging only on Refresh or when it is older than the TTL."""
    if ctx.database is None:
        return None
    force = st.session_state.pop(FORCE_KEY, False)
    status: ConnectionStatus | None = st.session_state.get(STATE_KEY)
    age = (datetime.now().astimezone() - status.checked_at).total_seconds() if status else None
    if force or status is None or age > STATUS_TTL_SECONDS:
        status = ctx.database.ping()
        st.session_state[STATE_KEY] = status
        if status.connected:  # a failed check keeps the previous success time
            st.session_state[LAST_SUCCESS_KEY] = status.checked_at
    return status


def last_success_at() -> datetime | None:
    """Return when a connection check last succeeded in this session."""
    return st.session_state.get(LAST_SUCCESS_KEY)


def _pill(conn: ConnectionStatus | None) -> tuple[str, str, list[str]]:
    """Return (css class, title, detail lines) for the connection indicator."""
    if conn is None:
        return "fi-warn", "Not configured", ["Database settings are missing or invalid"]
    if not conn.connected:
        success = last_success_at()
        last = f"Last successful check {success.strftime(TIME_FORMAT)}" if success else "No successful check yet"
        return "fi-bad", "MySQL not reachable", [conn.error or "Connection failed", last]
    detail = f"{conn.database}, server {conn.server_version}, {conn.latency_ms} ms"
    return "fi-ok", "MySQL connected", [detail]


def render_top_bar(ctx: AppContext) -> ConnectionStatus | None:
    """Render the brand, database status, refresh timestamp, and refresh action."""
    status = current_status(ctx)
    css, title, lines = _pill(status)

    left, middle, stamp, button = st.columns([2.8, 4.5, 2.3, 1.2], vertical_alignment="center")
    with left:
        st.markdown(
            f'<div class="fi-wordmark"><div class="fi-bar"></div><div>'
            f'<div class="fi-wm-title">{escape(APP_NAME)}</div>'
            f'<div class="fi-wm-sub">LOGISTICS · CONTROL DESK</div></div></div>',
            unsafe_allow_html=True,
        )
    with middle:
        subs = "".join(f'<div class="fi-pill-sub">{escape(line)}</div>' for line in lines)
        st.markdown(
            f'<div class="fi-pill {css}"><span class="fi-dot"></span><div>'
            f'<div class="fi-pill-title">{escape(title)}</div>{subs}</div></div>',
            unsafe_allow_html=True,
        )
    with stamp:
        value = status.checked_at.strftime(TIME_FORMAT) if status else "Not refreshed"
        st.markdown(
            f'<div><div class="fi-stamp-label">Last refreshed</div>'
            f'<div class="fi-stamp-value">{escape(value)}</div></div>',
            unsafe_allow_html=True,
        )
    with button:
        st.button("Refresh data", icon=":material/refresh:", key="fi_refresh", on_click=_on_refresh, args=(ctx,), width="stretch")
    return status
