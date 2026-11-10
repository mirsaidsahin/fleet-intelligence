"""Reusable panels that show connection, schema and configuration state."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from models.health import HealthReport
from models.schema_spec import EXPECTED_SCHEMA
from utils.config import ALL_VARS, REQUIRED_VARS, Settings, configuration_report

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


def connection_card(report: HealthReport | None, settings: Settings | None) -> None:
    if report is None:
        kv_card("Database connection", [("State", "Not configured", "fi-warn-text")])
        return
    conn = report.connection
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
    rows.append(
        ("Last successful", report.last_success_at.strftime(TIME_FORMAT) if report.last_success_at else "Never", "")
    )
    kv_card("Database connection", rows)


def schema_card(report: HealthReport | None) -> None:
    if report is None or report.schema is None:
        kv_card("Schema check", [("Result", "Not run", "fi-warn-text")])
        return
    s = report.schema
    result = ("Matches the expected schema", "fi-ok-text") if s.ok else ("Differs from the expected schema", "fi-warn-text")
    kv_card(
        "Schema check",
        [
            ("Tables", f"{s.tables_found} of {s.tables_expected}", ""),
            ("Views", f"{s.views_found} of {s.views_expected}", ""),
            ("Foreign keys", f"{s.foreign_keys_found} of {s.foreign_keys_expected}", ""),
            ("Result", *result),
        ],
    )


def schema_details(report: HealthReport | None) -> None:
    if report is None or report.schema is None:
        st.info("The schema check has not run yet.")
        return
    s = report.schema
    if s.error:
        st.error(s.error)
        return
    missing_cols = dict(s.missing_columns)
    rows = []
    for table, columns in EXPECTED_SCHEMA.tables.items():
        if table in s.missing_tables:
            result = "Table missing"
        elif table in missing_cols:
            result = "Missing columns: " + ", ".join(missing_cols[table])
        else:
            result = "OK"
        rows.append({"Object": table, "Kind": "Table", "Expected columns": str(len(columns)), "Result": result})
    for view in EXPECTED_SCHEMA.views:
        rows.append({"Object": view, "Kind": "View", "Expected columns": "n/a", "Result": "Missing" if view in s.missing_views else "OK"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    with st.expander("Foreign keys"):
        missing = set(s.missing_foreign_keys)
        fk_rows = [
            {"Relationship": fk.label(), "Result": "Missing" if fk.label() in missing else "OK"}
            for fk in EXPECTED_SCHEMA.foreign_keys
        ]
        st.dataframe(pd.DataFrame(fk_rows), hide_index=True, width="stretch")


def configuration_panel(settings: Settings | None, problems: tuple[str, ...] = ()) -> None:
    """Which settings exist. Shows names and set/not set only, never values."""
    status = configuration_report()
    rows = [
        {"Variable": name, "Required": "Yes" if name in REQUIRED_VARS else "No", "State": "Set" if status[name] else "Not set"}
        for name in ALL_VARS
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    if settings is not None:
        st.caption(f"Connection target: {settings.safe_dsn()}")
    for problem in problems:
        st.error(problem)
