"""Operations overview, dispatch board and driver scorecards."""
from __future__ import annotations

import base64
import hashlib
from datetime import datetime
from html import escape
from pathlib import Path

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

from components.bootstrap import get_app_context
from components.health_panels import connection_card, schema_card
from components.placeholders import page_header
from components.status_bar import current_report
from repositories.fleet import DashboardRepository
from services.image_assets import driver_image, truck_image
from utils.db import DatabaseUnavailableError, QueryError

FINLAND_NODES = {
    "Helsinki": (24.94, 60.17), "Riihimäki": (24.77, 60.74),
    "Tampere": (23.76, 61.50), "Turku": (22.27, 60.45),
    "Oulu": (25.47, 65.01), "Jyväskylä": (25.75, 62.24),
    "Vaasa": (21.62, 63.10), "Lahti": (25.66, 60.98),
    "Kotka": (26.94, 60.47), "Kouvola": (26.70, 60.87),
    "Kuopio": (27.68, 62.89), "Rovaniemi": (25.72, 66.50),
}
TRUCK_COLORS = ["#D69A4A", "#8FA37A", "#C77658", "#7D9AA5", "#B8A36A", "#9B8D7A", "#748A74"]


def _estimated_progress(job: dict) -> float:
    """Estimate route progress from the recorded start and route duration.

    This is a schedule-based estimate, not a GPS reading. If timing data is absent,
    a stable midpoint is used so refreshes never make a truck jump along its route.
    """
    start = pd.to_datetime(job.get("StartDate"), errors="coerce")
    try:
        duration_hours = float(job.get("EstimatedHours") or 0)
    except (TypeError, ValueError):
        duration_hours = 0
    if pd.notna(start) and duration_hours > 0:
        now = pd.Timestamp.now(tz=start.tz) if start.tz is not None else pd.Timestamp.now()
        elapsed_hours = max((now - start).total_seconds() / 3600, 0)
        return min(elapsed_hours / duration_hours, 0.98)

    seed = f"{job.get('TruckID')}:{job.get('JobID')}".encode("utf-8")
    value = int.from_bytes(hashlib.blake2s(seed, digest_size=4).digest(), "big") / 0xFFFFFFFF
    return 0.15 + value * 0.7


@st.cache_data(show_spinner=False)
def _image_data_uri(path: str, modified_ns: int) -> str:
    """Read local user-provided assets as data URIs for Folium hover previews."""
    del modified_ns  # participates in the cache key so replaced photos are refreshed
    image_path = Path(path)
    suffix = image_path.suffix.lower()
    mime = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"
    return f"data:{mime};base64,{base64.b64encode(image_path.read_bytes()).decode('ascii')}"


def _asset_uri(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    return _image_data_uri(str(path), path.stat().st_mtime_ns)


def _truck_tooltip(row: dict, progress: float, truck_color: str) -> str:
    brand_value = row.get("BrandID")
    brand_id = int(brand_value) if pd.notna(brand_value) else None
    truck_src = _asset_uri(truck_image(int(row["TruckID"]), brand_id, "tractor"))
    driver_src = _asset_uri(driver_image(int(row["DriverID"])))
    truck_photo = (f'<img src="{truck_src}" style="width:78px;height:52px;object-fit:contain;'
                   'background:#191D1B;border-radius:4px;padding:3px">' if truck_src else
                   '<div style="width:78px;height:52px;display:grid;place-items:center;background:#212724;'
                   'border-radius:4px;color:#A8AFA6;font-size:10px">TRUCK</div>')
    driver_photo = (f'<img src="{driver_src}" style="width:48px;height:48px;object-fit:cover;'
                    'border-radius:50%;border:2px solid #333A36">' if driver_src else
                    '<div style="width:48px;height:48px;border-radius:50%;background:#212724;display:grid;'
                    'place-items:center;color:#A8AFA6;font-size:10px">DRIVER</div>')
    truck = escape(str(row.get("Truck") or "Truck"))
    plate = escape(str(row.get("PlateNumber") or "—"))
    driver = escape(str(row.get("Driver") or "Unassigned"))
    route = f"{escape(str(row.get('DepartureCity')))} → {escape(str(row.get('ArrivalCity')))}"
    cargo = escape(str(row.get("CargoName") or "No cargo"))
    customer = escape(str(row.get("Customer") or "Unassigned"))
    return (
        '<div style="width:275px;padding:9px 10px;border-radius:6px;background:#191D1B;color:#ECEDE6;'
        'font:12px Bahnschrift,Segoe UI,sans-serif;border:1px solid #333A36;box-shadow:0 8px 26px #0008">'
        f'<div style="font-weight:700;color:{truck_color};font-size:14px;margin-bottom:7px">{truck} · {plate}</div>'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:7px">{truck_photo}{driver_photo}'
        f'<div><div style="font-weight:700">{driver}</div><div style="color:#A8AFA6">Job #{int(row["JobID"])}</div></div></div>'
        f'<div style="color:#ECEDE6">{route}</div>'
        f'<div style="color:#A8AFA6;margin-top:3px">{cargo} · {customer}</div>'
        f'<div style="color:#8FA37A;margin-top:6px;font-weight:700">ESTIMATED POSITION · {progress:.0%} OF ROUTE</div>'
        '</div>'
    )


def fleet_map(routes: pd.DataFrame, active_jobs: pd.DataFrame) -> tuple[folium.Map, list[dict]]:
    """Build a client-interactive street map without Streamlit reruns on map clicks."""
    map_view = folium.Map(location=[64.45, 26.0], zoom_start=5, tiles="OpenStreetMap",
                          control_scale=True, prefer_canvas=True, width="100%", height=570)
    mapped_cities: set[str] = set()
    route_line_refs: dict[str, str] = {}
    marker_refs: dict[str, str] = {}
    truck_colors: dict[str, str] = {}
    route_labels: dict[str, str] = {}
    if not routes.empty:
        for row in routes.to_dict("records"):
            start, end = row["DepartureCity"], row["ArrivalCity"]
            if start not in FINLAND_NODES or end not in FINLAND_NODES:
                continue
            x1, y1 = FINLAND_NODES[start]
            x2, y2 = FINLAND_NODES[end]
            mapped_cities.update((start, end))
            transit, pending = int(row["in_transit"] or 0), int(row["pending"] or 0)
            color = "#7D9AA5" if transit else ("#C77658" if pending else "#333A36")
            folium.PolyLine(
                [(y1, x1), (y2, x2)], color=color, weight=3 if transit or pending else 1.5,
                opacity=.66 if transit or pending else .35,
                tooltip=f"{escape(start)} → {escape(end)} · {int(row['DistanceKm'])} km · {transit} in transit · {pending} pending",
            ).add_to(map_view)

    active_records = active_jobs.to_dict("records") if not active_jobs.empty else []
    plotted_jobs: list[dict] = []
    for row in active_records:
        start, end = row.get("DepartureCity"), row.get("ArrivalCity")
        if start not in FINLAND_NODES or end not in FINLAND_NODES:
            continue
        progress = _estimated_progress(row)
        x1, y1 = FINLAND_NODES[start]
        x2, y2 = FINLAND_NODES[end]
        lon, lat = x1 + (x2 - x1) * progress, y1 + (y2 - y1) * progress
        position = {**row, "_lon": lon, "_lat": lat, "_progress": progress}
        plotted_jobs.append(position)
        mapped_cities.update((start, end))
        job_key = str(int(row["JobID"]))
        truck_color = TRUCK_COLORS[int(row["TruckID"]) % len(TRUCK_COLORS)]
        route_line = folium.PolyLine(
            [(y1, x1), (y2, x2)], color="#7D9AA5", weight=2.5, opacity=.62,
            tooltip=f"Job #{row['JobID']} · {escape(start)} → {escape(end)}",
        ).add_to(map_view)
        marker = folium.CircleMarker(
            location=[lat, lon], radius=8,
            color=truck_color, weight=3, fill=True, fill_color=truck_color, fill_opacity=.95,
            tooltip=folium.Tooltip(
                _truck_tooltip(row, progress, truck_color), sticky=True, direction="top", opacity=.99,
                style="border:0;background:transparent;box-shadow:none;padding:0;",
            ),
        ).add_to(map_view)
        route_line_refs[job_key] = route_line.get_name()
        marker_refs[job_key] = marker.get_name()
        truck_colors[job_key] = truck_color
        route_labels[job_key] = (
            f"Job #{row['JobID']} · {row.get('Truck') or 'Truck'} · "
            f"{start} → {end} · Driver: {row.get('Driver') or 'Unassigned'}"
        )

    cities = sorted(mapped_cities)
    if cities:
        for city in cities:
            lon, lat = FINLAND_NODES[city]
            folium.CircleMarker(
                [lat, lon], radius=4, color="#ECEDE6", weight=1,
                fill=True, fill_color="#ECEDE6", fill_opacity=.9,
                tooltip=city,
            ).add_to(map_view)
    if plotted_jobs:
        import json

        route_lines_json = json.dumps(route_line_refs)
        markers_json = json.dumps(marker_refs)
        colors_json = json.dumps(truck_colors)
        labels_json = json.dumps(route_labels, ensure_ascii=False).replace("</", "<\\/")
        map_name = map_view.get_name()
        script = f"""
(function() {{
  const map = {map_name};
  const routeLines = {route_lines_json};
  const truckMarkers = {markers_json};
  const baseColors = {colors_json};
  const routeLabels = {labels_json};
  let picker, selectedLabel;
  function selectRoute(id) {{
    Object.keys(routeLines).forEach(function(key) {{
      routeLines[key].setStyle({{color:'#7D9AA5', weight:2.5, opacity:.62}});
      truckMarkers[key].setStyle({{color:baseColors[key], fillColor:baseColors[key], radius:8}});
    }});
    if (routeLines[id]) {{
      routeLines[id].setStyle({{color:'#D69A4A', weight:6, opacity:.98}});
      routeLines[id].bringToFront();
      truckMarkers[id].setStyle({{color:'#D69A4A', fillColor:'#D69A4A', radius:11}});
      truckMarkers[id].bringToFront();
      selectedLabel.textContent = routeLabels[id];
    }} else {{
      selectedLabel.textContent = 'No route highlighted';
    }}
    picker.value = id || '';
  }}
  const routeControl = L.control({{position:'topright'}});
  routeControl.onAdd = function() {{
    const box = L.DomUtil.create('div', 'fi-route-control');
    box.style.cssText = 'width:280px;padding:10px 11px;background:#191D1B;border:1px solid #333A36;border-radius:6px;color:#ECEDE6;box-shadow:0 3px 14px #0008;font:12px Bahnschrift,Aptos,Segoe UI,sans-serif';
    box.innerHTML = '<div style="font-weight:700;color:#D69A4A;margin:0 0 6px">TRUCK ROUTE</div><select style="width:100%;padding:7px 8px;border-radius:4px;background:#212724;color:#ECEDE6;border:1px solid #333A36"><option value="">Choose a vehicle</option></select><div class="fi-route-selected" style="margin-top:6px;color:#A8AFA6;line-height:1.4">No route selected</div>';
    picker = box.querySelector('select');
    selectedLabel = box.querySelector('.fi-route-selected');
    Object.keys(routeLines).forEach(function(key) {{
      const option = document.createElement('option');
      option.value = key;
      option.textContent = routeLabels[key];
      picker.appendChild(option);
      truckMarkers[key].on('click', function() {{ selectRoute(key); }});
    }});
    picker.addEventListener('change', function() {{ selectRoute(this.value); }});
    L.DomEvent.disableClickPropagation(box);
    L.DomEvent.disableScrollPropagation(box);
    return box;
  }};
  routeControl.addTo(map);
}})();
"""
        map_view.get_root().script.add_child(folium.Element(script))
    return map_view, plotted_jobs


@st.fragment(run_every="10m")
def render_fleet_map_panel(routes: pd.DataFrame, active_jobs: pd.DataFrame) -> None:
    """Render a self-contained map whose route interactions stay in the browser."""
    map_view, plotted_jobs = fleet_map(routes, active_jobs)
    st_folium(
        map_view, height=590, width=None, use_container_width=True,
        key="command_center_static_fleet_map", returned_objects=[],
    )
    st.markdown(
        '<div class="fi-map-legend"><span><i class="fi-legend-dot fi-legend-trucks"></i>Vehicles in transit</span>'
        '<span><i class="fi-legend-line"></i>Selected route</span>'
        '<span class="fi-map-disclaimer">Schedule-based estimates · not GPS · refreshes every 10 minutes</span></div>',
        unsafe_allow_html=True,
    )
    if not plotted_jobs:
        st.caption("There are no in-transit trucks to plot right now. Route lanes still show the operating network.")
    st.caption("Hover a colored point for the truck and driver photo preview; click a point or use the map’s route selector to switch highlights instantly.")


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
                     color="On-time %", color_continuous_scale=["#C77658", "#D69A4A", "#8FA37A"],
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
    active_jobs = pd.DataFrame(repo.active_truck_positions())
    alerts = pd.DataFrame(repo.operational_alerts())

    st.markdown(
        f'<div class="fi-hero"><div class="fi-eyebrow">OMNILOGISTICS · DISPATCH DESK</div>'
        f'<div class="fi-hero-title">Today’s network</div>'
        f'<div class="fi-hero-sub">Operations briefing · {datetime.now():%A, %d %B %Y}</div></div>',
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
        with st.container(border=True):
            alert_count = len(alerts)
            count_text = f"{alert_count} OPEN ITEM{'S' if alert_count != 1 else ''}" if alert_count else "RULES CLEAR"
            st.markdown(
                f'<div class="fi-attention-head"><div class="fi-attention-title">Operational attention</div>'
                f'<div class="fi-attention-count">{count_text}</div></div>',
                unsafe_allow_html=True,
            )
            if alerts.empty:
                st.success("No dispatch review is needed right now.")
                st.caption("Rule checks cover pending jobs past their start time and in-transit jobs beyond the route estimate.")
            else:
                st.caption("Rule-based exceptions from live job and route records. Review these with dispatch.")
                visible_alerts = alerts.head(4).to_dict("records")
                alert_columns = st.columns(2, gap="small")
                for index, row in enumerate(visible_alerts):
                    with alert_columns[index % 2]:
                        st.markdown(
                            f'<div class="fi-alert"><div class="fi-alert-title">JOB #{int(row["JobID"])} · {escape(str(row["Alert"]))}</div>'
                            f'<div class="fi-alert-detail">{escape(str(row["Route"]))}</div>'
                            f'<div class="fi-alert-detail">Driver: {escape(str(row["Driver"]))} · Suggested action: {escape(str(row["Action"]))}</div></div>',
                            unsafe_allow_html=True,
                        )
                if alert_count > 4:
                    with st.expander(f"Show {alert_count - 4} more review items"):
                        for row in alerts.iloc[4:].to_dict("records"):
                            st.markdown(
                                f'<div class="fi-alert"><div class="fi-alert-title">JOB #{int(row["JobID"])} · {escape(str(row["Alert"]))}</div>'
                                f'<div class="fi-alert-detail">{escape(str(row["Route"]))} · Driver: {escape(str(row["Driver"]))} · {escape(str(row["Action"]))}</div></div>',
                                unsafe_allow_html=True,
                            )

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
                fig.update_layout(height=340, margin={"l": 4, "r": 8, "t": 8, "b": 8,
                                                     "pad": 0}, showlegend=False,
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
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
