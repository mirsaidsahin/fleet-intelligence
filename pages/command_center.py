"""Operations overview and dispatch board."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from components.bootstrap import get_app_context
from components.fleet_map import render_fleet_map_panel
from components.ui import page_header, search_frame
from repositories.fleet import DashboardRepository
from utils.db import DatabaseUnavailableError, QueryError

TRANSPARENT = {"paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)"}


def _dispatch_view(repo: DashboardRepository) -> None:
    """Show searchable open assignments and export the current filtered view."""
    st.subheader("Live dispatch board")
    st.caption("Open jobs from MySQL, grouped by current operational status.")
    frame = pd.DataFrame(repo.dispatch_board())
    if frame.empty:
        st.info("No open jobs are scheduled.")
        return
    statuses = frame["Status"].dropna().unique().tolist()
    first, second = st.columns([1, 2])
    with first:
        selected_statuses = st.multiselect("Status", statuses, default=statuses, key="dispatch_status")
    with second:
        search = st.text_input("Find a truck, driver, route or customer", key="dispatch_search")
    frame = search_frame(frame[frame["Status"].isin(selected_statuses)], search)
    st.caption(f"{len(frame)} job(s) match the current view")
    st.dataframe(frame, hide_index=True, width="stretch", column_config={
        "StartDate": st.column_config.DatetimeColumn("Start time", format="D MMM, HH:mm"),
        "DistanceKm": st.column_config.NumberColumn("Distance", format="%d km"),
        "JobID": st.column_config.NumberColumn("Job", format="#%d"),
    })
    st.download_button("Export dispatch board", frame.to_csv(index=False).encode("utf-8-sig"),
                       "dispatch_board.csv", "text/csv", disabled=frame.empty)


ctx = get_app_context()
page_header("Operations Command Center", "One live view for fleet readiness, route activity and dispatch risks.")

if ctx.database is None:
    st.info("Set the database values in `.env` to show operating data.")
    st.page_link("pages/system.py", label="Open System")
    st.stop()

try:
    # Load the dashboard's independent datasets once for this page run.
    repo = DashboardRepository(ctx.database)
    stats = repo.summary()
    trucks = pd.DataFrame(repo.truck_statuses())
    active_jobs = pd.DataFrame(repo.active_truck_positions())

    st.markdown(
        f'<div class="fi-hero"><div class="fi-eyebrow">OMNILOGISTICS · DISPATCH DESK</div>'
        f'<div class="fi-hero-title">Today’s network</div>'
        f'<div class="fi-hero-sub">Operations briefing · {datetime.now():%A, %d %B %Y}</div></div>',
        unsafe_allow_html=True,
    )
    fleet_count = int(stats.get("trucks") or 0)
    in_service = int(stats.get("in_transit") or 0)
    a, b, c, d, e = st.columns(5)
    a.metric("Fleet vehicles", f"{fleet_count:,}")
    b.metric("Drivers", f"{int(stats.get('drivers') or 0):,}")
    c.metric("Open jobs", f"{int(stats.get('open_jobs') or 0):,}")
    d.metric("In transit", f"{in_service:,}")
    e.metric("Pending past start", f"{int(stats.get('overdue') or 0):,}", help="Pending jobs whose recorded start time has passed")
    utilization = round(100 * in_service / fleet_count) if fleet_count else 0
    st.progress(min(utilization, 100), text=f"Fleet currently in transit · {in_service} of {fleet_count} vehicles ({utilization}%)")

    overview_tab, dispatch_tab = st.tabs(["Network overview", "Dispatch board"])
    with overview_tab:
        map_col, allocation_col = st.columns([1.5, 1], gap="large")
        with map_col:
            st.subheader("Fleet map · estimated truck positions")
            routes = pd.DataFrame(repo.route_network())
            if routes.empty:
                st.info("No routes are available.")
            else:
                render_fleet_map_panel(routes, active_jobs)
                st.dataframe(routes[["DepartureCity", "ArrivalCity", "DistanceKm", "EstimatedHours", "in_transit", "pending"]],
                             hide_index=True, width="stretch", column_config={
                    "DistanceKm": st.column_config.NumberColumn("Distance", format="%d km"),
                    "EstimatedHours": st.column_config.NumberColumn("Estimate", format="%.1f h"),
                    "in_transit": st.column_config.NumberColumn("On route", format="%d"),
                    "pending": st.column_config.NumberColumn("Pending", format="%d"),
                })
        with allocation_col:
            st.subheader("Fleet status")
            if not trucks.empty:
                counts = trucks["Status"].astype(str).value_counts().rename_axis("Status").reset_index(name="Vehicles")
                display_status = {
                    "Needs Review": "Past-start review",
                    "Conflict": "Assignment conflict",
                }
                counts["Status"] = counts["Status"].replace(display_status)
                review_count = int(counts.loc[counts["Status"] == "Past-start review", "Vehicles"].sum())
                if review_count:
                    st.caption(
                        f"{review_count} trucks have a pending job whose planned start time has passed. "
                        "Dispatch should confirm or reschedule these assignments."
                    )
                fig = px.bar(counts, x="Vehicles", y="Status", orientation="h", color="Status",
                             color_discrete_map={"In Transit": "#7D9AA5", "Available": "#8FA37A",
                                                 "Scheduled": "#D69A4A", "Past-start review": "#C77658",
                                                 "Assignment conflict": "#9B8D7A"})
                fig.update_traces(marker_line_width=0, text=counts["Vehicles"], textposition="outside",
                                  cliponaxis=False, textfont={"color": "#ECEDE6", "size": 12})
                fig.update_layout(height=340, margin={"l": 4, "r": 8, "t": 8, "b": 8, "pad": 0}, showlegend=False,
                                  **TRANSPARENT,
                                  font={"family": "Bahnschrift, Aptos, Segoe UI, sans-serif", "color": "#ECEDE6"},
                                  xaxis={"showgrid": True, "gridcolor": "#333A36", "zeroline": False,
                                         "title": "Trucks", "range": [0, max(int(counts["Vehicles"].max()) * 1.25, 1)]},
                                  yaxis={"title": "", "categoryorder": "total ascending"})
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        rev_col, recent_col = st.columns([1, 1.2])
        with rev_col:
            st.subheader("Completed revenue")
            st.metric("Recorded total", f"€{float(stats.get('completed_revenue') or 0):,.2f}")
            monthly = pd.DataFrame(repo.monthly_revenue())
            if not monthly.empty:
                fig = px.area(monthly, x="month", y="revenue", markers=True,
                              labels={"month": "Month", "revenue": "Revenue (EUR)"})
                fig.update_traces(line_color="#D69A4A", fillcolor="rgba(214,154,74,.14)")
                fig.update_layout(height=300, margin={"l": 8, "r": 8, "t": 12, "b": 8, "pad": 0},
                                  **TRANSPARENT)
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            else:
                st.info("No completed revenue records yet.")
        with recent_col:
            st.subheader("Latest activity")
            recent = pd.DataFrame(repo.recent_jobs(8))
            if recent.empty:
                st.info("No job records found.")
            else:
                st.dataframe(recent, hide_index=True, width="stretch", column_config={
                    "StartDate": st.column_config.DatetimeColumn("Start", format="D MMM, HH:mm"),
                    "RevenueEUR": st.column_config.NumberColumn("Revenue", format="€%.2f"),
                })

    with dispatch_tab:
        _dispatch_view(repo)
except (DatabaseUnavailableError, QueryError) as exc:
    st.error(str(exc))
