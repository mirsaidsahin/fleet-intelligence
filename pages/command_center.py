"""Operations overview, dispatch board and driver scorecards."""
from __future__ import annotations

from datetime import datetime
from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.bootstrap import get_app_context
from components.health_panels import connection_card, schema_card
from components.placeholders import page_header
from components.status_bar import current_report
from repositories.fleet import DashboardRepository
from utils.db import DatabaseUnavailableError, QueryError

FINLAND_NODES = {
    "Helsinki": (24.94, 60.17), "Riihimäki": (24.77, 60.74),
    "Tampere": (23.76, 61.50), "Turku": (22.27, 60.45),
    "Oulu": (25.47, 65.01), "Jyväskylä": (25.75, 62.24),
    "Vaasa": (21.62, 63.10), "Lahti": (25.66, 60.98),
    "Kotka": (26.94, 60.47), "Kouvola": (26.70, 60.87),
    "Kuopio": (27.68, 62.89), "Rovaniemi": (25.72, 66.50),
}


def route_figure(routes: pd.DataFrame) -> go.Figure:
    """Draw an offline route schematic from live route rows and real city positions."""
    fig = go.Figure()
    if routes.empty:
        return fig
    max_load = max(1, int((routes["in_transit"] + routes["pending"]).max()))
    for row in routes.to_dict("records"):
        start, end = row["DepartureCity"], row["ArrivalCity"]
        if start not in FINLAND_NODES or end not in FINLAND_NODES:
            continue
        x1, y1 = FINLAND_NODES[start]
        x2, y2 = FINLAND_NODES[end]
        transit, pending = int(row["in_transit"] or 0), int(row["pending"] or 0)
        color = "#F2A33A" if transit else ("#E5484D" if pending else "#56616D")
        fig.add_trace(go.Scatter(
            x=[x1, x2], y=[y1, y2], mode="lines",
            line={"color": color, "width": 1.5 + 2.5 * (transit + pending) / max_load},
            customdata=[[start, end, row["DistanceKm"], transit, pending]] * 2,
            hovertemplate="%{customdata[0]} → %{customdata[1]}<br>%{customdata[2]} km"
                          "<br>In transit: %{customdata[3]} · Pending: %{customdata[4]}<extra></extra>",
            showlegend=False,
        ))
    used = {city for row in routes.to_dict("records")
            for city in (row["DepartureCity"], row["ArrivalCity"])
            if city in FINLAND_NODES}
    cities = sorted(used)
    fig.add_trace(go.Scatter(
        x=[FINLAND_NODES[name][0] for name in cities],
        y=[FINLAND_NODES[name][1] for name in cities],
        mode="markers+text", text=cities, textposition="top center",
        textfont={"size": 10, "color": "#D6DBE1"},
        marker={"size": 9, "color": "#F2A33A", "line": {"width": 1, "color": "#17191C"}},
        hovertemplate="%{text}<extra>Route city</extra>", showlegend=False,
    ))
    fig.update_layout(
        height=420, margin={"l": 8, "r": 8, "t": 8, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False, "range": [20.5, 28.8]},
        yaxis={"visible": False, "range": [59.8, 67.0], "scaleanchor": "x", "scaleratio": 1.15},
        hoverlabel={"bgcolor": "#20242A", "font": {"color": "#E8E9EB"}},
    )
    return fig


def _dispatch_view(repo: DashboardRepository) -> None:
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
    frame = frame[frame["Status"].isin(selected_statuses)]
    if search.strip():
        mask = frame.astype(str).apply(lambda col: col.str.contains(search.strip(), case=False, na=False)).any(axis=1)
        frame = frame[mask]
    st.caption(f"{len(frame)} job(s) match the current view")
    st.dataframe(frame, hide_index=True, width="stretch", column_config={
        "StartDate": st.column_config.DatetimeColumn("Start time", format="D MMM, HH:mm"),
        "DistanceKm": st.column_config.NumberColumn("Distance", format="%d km"),
        "JobID": st.column_config.NumberColumn("Job", format="#%d"),
    })
    st.download_button("Export dispatch board", frame.to_csv(index=False).encode("utf-8-sig"),
                       "dispatch_board.csv", "text/csv", disabled=frame.empty)


def _driver_view(repo: DashboardRepository) -> None:
    st.subheader("Driver performance")
    st.caption("Completed jobs, revenue and distance are aggregated from recorded job data."
               " On-time means the recorded finish is within the route estimate.")
    frame = pd.DataFrame(repo.driver_scoreboard())
    if frame.empty:
        st.info("No driver records are available.")
        return
    frame["On-time %"] = frame.apply(
        lambda row: round(100 * int(row["OnTimeJobs"]) / int(row["CompletedJobs"]), 1)
        if int(row["CompletedJobs"] or 0) else None, axis=1,
    )
    active = frame[frame["CompletedJobs"] > 0].copy()
    if not active.empty:
        leader = active.iloc[0]
        one, two, three = st.columns(3)
        one.metric("Most completed jobs", leader["Driver"], f"{int(leader['CompletedJobs'])} completed")
        two.metric("Recorded revenue", f"€{float(active['RevenueEUR'].sum()):,.0f}")
        three.metric("Distance driven", f"{int(active['DistanceKm'].sum()):,} km")
        chart = active.head(10).sort_values("On-time %", ascending=True)
        fig = px.bar(chart, x="On-time %", y="Driver", orientation="h", text="On-time %",
                     color="On-time %", color_continuous_scale=["#D95C59", "#F2A33A", "#4FA66B"],
                     range_color=[0, 100])
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False)
        fig.update_layout(height=360, margin={"l": 8, "r": 34, "t": 12, "b": 8},
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          coloraxis_showscale=False, xaxis={"range": [0, 112], "ticksuffix": "%"})
        st.plotly_chart(fig, width="stretch")
    view = frame[["Driver", "ExperienceYears", "CompletedJobs", "OnTimeJobs", "On-time %", "RevenueEUR", "DistanceKm"]].copy()
    view.columns = ["Driver", "Experience (years)", "Completed jobs", "On-time jobs", "On-time %", "Revenue (EUR)", "Distance (km)"]
    st.dataframe(view, hide_index=True, width="stretch", column_config={
        "Revenue (EUR)": st.column_config.NumberColumn(format="€%.2f"),
        "Distance (km)": st.column_config.NumberColumn(format="%d km"),
        "On-time %": st.column_config.NumberColumn(format="%.1f%%"),
    })


ctx = get_app_context()
report = current_report(ctx)
page_header("Operations Command Center", "One live view for fleet readiness, route activity and dispatch risks.")

if ctx.database is None:
    left, right = st.columns(2)
    with left:
        connection_card(report, ctx.settings)
    with right:
        schema_card(report)
    st.info("Set the database values in `.env` to show operating data.")
    st.page_link("pages/reports_system.py", label="Open Reports & System")
    st.stop()

try:
    repo = DashboardRepository(ctx.database)
    stats = repo.summary()
    trucks = pd.DataFrame(repo.truck_statuses())
    alerts = pd.DataFrame(repo.operational_alerts())

    st.markdown(
        f'<div class="fi-hero"><div class="fi-eyebrow">OMNILOGISTICS · OPERATIONS INTELLIGENCE</div>'
        f'<div class="fi-hero-title">Fleet at a glance</div>'
        f'<div class="fi-hero-sub">Operational snapshot · {datetime.now():%A, %d %B %Y}</div></div>',
        unsafe_allow_html=True,
    )
    a, b, c, d, e = st.columns(5)
    a.metric("Fleet vehicles", f"{int(stats.get('trucks') or 0):,}")
    b.metric("Drivers", f"{int(stats.get('drivers') or 0):,}")
    c.metric("Open jobs", f"{int(stats.get('open_jobs') or 0):,}")
    d.metric("In transit", f"{int(stats.get('in_transit') or 0):,}")
    e.metric("Pending past start", f"{int(stats.get('overdue') or 0):,}", help="Pending jobs whose recorded start time has passed")
    fleet_count = int(stats.get("trucks") or 0)
    in_service = int(stats.get("in_transit") or 0)
    utilization = round(100 * in_service / fleet_count) if fleet_count else 0
    st.progress(min(utilization, 100), text=f"Fleet currently in transit · {in_service} of {fleet_count} vehicles ({utilization}%)")

    overview_tab, dispatch_tab, drivers_tab = st.tabs(["Network overview", "Dispatch board", "Driver performance"])
    with overview_tab:
        map_col, alert_col = st.columns([1.45, 1])
        with map_col:
            st.subheader("Route network")
            routes = pd.DataFrame(repo.route_network())
            if routes.empty:
                st.info("No routes are available.")
            else:
                st.plotly_chart(route_figure(routes), width="stretch", config={"displayModeBar": False})
                st.caption("Route paths and workload come from MySQL. City positions are approximate; map renders offline.")
                st.dataframe(routes[["DepartureCity", "ArrivalCity", "DistanceKm", "EstimatedHours", "in_transit", "pending"]],
                             hide_index=True, width="stretch", column_config={
                    "DistanceKm": st.column_config.NumberColumn("Distance", format="%d km"),
                    "EstimatedHours": st.column_config.NumberColumn("Estimate", format="%.1f h"),
                    "in_transit": st.column_config.NumberColumn("On route", format="%d"),
                    "pending": st.column_config.NumberColumn("Pending", format="%d"),
                })
        with alert_col:
            st.subheader("Operational attention")
            if alerts.empty:
                st.success("No rule-based alerts right now.")
                st.caption("Checks: pending jobs past start and in-transit jobs beyond the route estimate.")
            else:
                st.warning(f"{len(alerts)} item(s) need a dispatch review.")
                for row in alerts.to_dict("records"):
                    st.markdown(
                        f'<div class="fi-alert"><div class="fi-alert-title">JOB #{int(row["JobID"])} · {escape(str(row["Alert"]))}</div>'
                        f'<div class="fi-alert-detail">{escape(str(row["Route"]))}</div>'
                        f'<div class="fi-alert-detail">Driver: {escape(str(row["Driver"]))} · {escape(str(row["Action"]))}</div></div>',
                        unsafe_allow_html=True,
                    )
            st.subheader("Fleet allocation")
            if not trucks.empty:
                counts = trucks["Status"].astype(str).value_counts().rename_axis("Status").reset_index(name="Vehicles")
                fig = px.bar(counts, x="Vehicles", y="Status", orientation="h", color="Status",
                             color_discrete_map={"In Transit": "#F2A33A", "Available": "#4FA66B",
                                                 "Scheduled": "#4C88C7", "Needs Review": "#E5484D", "Conflict": "#B04ACB"})
                fig.update_layout(height=300, margin={"l": 4, "r": 8, "t": 8, "b": 8,
                                                     "pad": 0}, showlegend=False,
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        rev_col, recent_col = st.columns([1, 1.2])
        with rev_col:
            st.subheader("Completed revenue")
            st.metric("Recorded total", f"€{float(stats.get('completed_revenue') or 0):,.2f}")
            monthly = pd.DataFrame(repo.monthly_revenue())
            if not monthly.empty:
                fig = px.area(monthly, x="month", y="revenue", markers=True,
                              labels={"month": "Month", "revenue": "Revenue (EUR)"})
                fig.update_traces(line_color="#F2A33A", fillcolor="rgba(242,163,58,.12)")
                fig.update_layout(height=300, margin={"l": 8, "r": 8, "t": 12, "b": 8,
                                                      "pad": 0},
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
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
    with drivers_tab:
        _driver_view(repo)

    with st.expander("Database health"):
        x, y = st.columns(2)
        with x:
            connection_card(report, ctx.settings)
        with y:
            schema_card(report)
except (DatabaseUnavailableError, QueryError) as exc:
    st.error(str(exc))
