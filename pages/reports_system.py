"""System health details and downloadable operational reports."""
import pandas as pd
import streamlit as st

from components.bootstrap import get_app_context
from components.health_panels import configuration_panel, connection_card, schema_card, schema_details
from components.placeholders import page_header
from components.status_bar import current_report
from components.tables import search_frame
from repositories.fleet import FleetRepository
from utils.db import DatabaseUnavailableError, QueryError
from utils.version import APP_NAME, APP_VERSION, BUILD_PHASE

ctx = get_app_context()
report = current_report(ctx)

page_header("Reports & System", "Connection, schema and configuration checks")

system_tab, reports_tab = st.tabs(["System", "Reports"])

with system_tab:
    # Pair the live connection summary with schema and configuration details.
    left, right = st.columns(2)
    with left:
        connection_card(report, ctx.settings)
    with right:
        schema_card(report)
    st.subheader("Schema details")
    schema_details(report)
    st.subheader("Configuration")
    configuration_panel(ctx.settings, ctx.config_problems)
    st.caption(f"{APP_NAME} {APP_VERSION}, {BUILD_PHASE}")

with reports_tab:
    # Export only the selected table and apply optional filters before download.
    st.subheader("Operational data export")
    if ctx.database is None:
        st.info("Configure the database connection to build reports.")
    else:
        table = st.selectbox("Report", ["jobs", "trucks", "drivers", "customers", "routes", "cargos"])
        try:
            frame = pd.DataFrame(FleetRepository(ctx.database).rows(table))
            if not frame.empty:
                if table == "jobs" and "Status" in frame:
                    statuses = sorted(frame["Status"].dropna().unique().tolist())
                    selected = st.multiselect("Job status", statuses, default=statuses)
                    frame = frame[frame["Status"].isin(selected)]
                search = st.text_input("Filter report", placeholder="Search across the displayed fields")
                frame = search_frame(frame, search)
            st.caption(f"{len(frame)} record(s) · maximum 500 per report")
            st.dataframe(frame, hide_index=True, width="stretch")
            st.download_button("Download CSV", data=frame.to_csv(index=False).encode("utf-8-sig"), file_name=f"fleet_{table}.csv", mime="text/csv", disabled=frame.empty)
        except (DatabaseUnavailableError, QueryError) as exc:
            st.error(str(exc))
