"""Top status bar. Everything shown comes from a real check; nothing is labelled live."""
from __future__ import annotations

from datetime import datetime
from html import escape

import streamlit as st

from components.bootstrap import AppContext, get_app_context
from models.health import HealthReport
from utils.version import APP_NAME

STATE_KEY = "fi_health_report"
FORCE_KEY = "fi_force_refresh"
TIME_FORMAT = "%d %b %Y · %H:%M"


def _on_refresh(ctx: AppContext) -> None:
    """Mark cached dashboard data stale and reload settings when needed."""
    st.session_state[FORCE_KEY] = True
    st.cache_data.clear()  # read caches added in later phases are dropped here too
    if ctx.settings is None:
        get_app_context.clear()  # re-read .env after the user fixed it


def current_report(ctx: AppContext) -> HealthReport | None:
    """Return the latest HealthReport, re-checking only on Refresh or when it is older than the TTL."""
    if ctx.health is None or ctx.settings is None:
        return None
    force = st.session_state.pop(FORCE_KEY, False)
    report: HealthReport | None = st.session_state.get(STATE_KEY)
    age = (datetime.now().astimezone() - report.refreshed_at).total_seconds() if report else None
    if force or report is None or age > ctx.settings.status_ttl_seconds:
        report = ctx.health.check(report, verify_schema=force or report is None)
        st.session_state[STATE_KEY] = report
    return report


def _pill(report: HealthReport | None) -> tuple[str, str, list[str]]:
    """Return (css class, title, detail lines) for the connection indicator."""
    if report is None:
        return "fi-warn", "Not configured", ["Database settings are missing or invalid"]
    conn = report.connection
    if not conn.connected:
        last = (
            f"Last successful check {report.last_success_at.strftime(TIME_FORMAT)}"
            if report.last_success_at
            else "No successful check yet"
        )
        return "fi-bad", "MySQL not reachable", [conn.error or "Connection failed", last]
    detail = f"{conn.database}, server {conn.server_version}, {conn.latency_ms} ms"
    if report.schema is not None and not report.schema.ok:
        first = report.schema.problems()[0]
        return "fi-warn", "Connected, schema differs", [detail, first]
    return "fi-ok", "MySQL connected", [detail]


def render_top_bar(ctx: AppContext) -> HealthReport | None:
    """Render the brand, database status, refresh timestamp, and refresh action."""
    report = current_report(ctx)
    css, title, lines = _pill(report)

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
        value = report.refreshed_at.strftime(TIME_FORMAT) if report else "Not refreshed"
        st.markdown(
            f'<div><div class="fi-stamp-label">Last refreshed</div>'
            f'<div class="fi-stamp-value">{escape(value)}</div></div>',
            unsafe_allow_html=True,
        )
    with button:
        st.button("Refresh data", icon=":material/refresh:", key="fi_refresh", on_click=_on_refresh, args=(ctx,), width="stretch")
    return report
