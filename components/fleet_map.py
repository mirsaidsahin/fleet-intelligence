"""Folium fleet map and its Streamlit panel for the command center."""
from __future__ import annotations

import random
from html import escape

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

FINLAND_NODES = {
    # Fixed illustrative coordinates keep the demo map independent of geocoding.
    "Helsinki": (24.94, 60.17), "Riihimäki": (24.77, 60.74),
    "Tampere": (23.76, 61.50), "Turku": (22.27, 60.45),
    "Oulu": (25.47, 65.01), "Jyväskylä": (25.75, 62.24),
    "Vaasa": (21.62, 63.10), "Lahti": (25.66, 60.98),
    "Kotka": (26.94, 60.47), "Kouvola": (26.70, 60.87),
    "Kuopio": (27.68, 62.89), "Rovaniemi": (25.72, 66.50),
}
TRUCK_COLORS = ["#D69A4A", "#8FA37A", "#C77658", "#7D9AA5", "#B8A36A", "#9B8D7A", "#748A74"]


def _truck_tooltip(row: dict, progress: float, truck_color: str) -> str:
    """Build an escaped hover card for a truck, driver, route, and cargo."""
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
        f'<div style="margin-bottom:7px"><div style="font-weight:700">{driver}</div><div style="color:#A8AFA6">Job #{int(row["JobID"])}</div></div>'
        f'<div style="color:#ECEDE6">{route}</div>'
        f'<div style="color:#A8AFA6;margin-top:3px">{cargo} · {customer}</div>'
        f'<div style="color:#8FA37A;margin-top:6px;font-weight:700">ILLUSTRATIVE POSITION · {progress:.0%} OF ROUTE</div>'
        '</div>'
    )


def fleet_map(routes: pd.DataFrame, active_jobs: pd.DataFrame) -> tuple[folium.Map, list[dict]]:
    """Build the street map with route lines, truck markers and tooltips."""
    map_view = folium.Map(location=[64.45, 26.0], zoom_start=5, tiles="OpenStreetMap",
                          control_scale=True, prefer_canvas=True, width="100%", height=570)
    mapped_cities: set[str] = set()
    if not routes.empty:
        # Draw route-network lanes first so truck markers remain easy to see.
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
        # Skip unsupported city pairs instead of placing markers at false coordinates.
        start, end = row.get("DepartureCity"), row.get("ArrivalCity")
        if start not in FINLAND_NODES or end not in FINLAND_NODES:
            continue
        # A fresh illustrative point on each render; not derived from schedule or GPS data.
        progress = random.uniform(0.15, 0.85)
        x1, y1 = FINLAND_NODES[start]
        x2, y2 = FINLAND_NODES[end]
        lon, lat = x1 + (x2 - x1) * progress, y1 + (y2 - y1) * progress
        position = {**row, "_lon": lon, "_lat": lat, "_progress": progress}
        plotted_jobs.append(position)
        mapped_cities.update((start, end))
        truck_color = TRUCK_COLORS[int(row["TruckID"]) % len(TRUCK_COLORS)]
        folium.PolyLine(
            [(y1, x1), (y2, x2)], color="#7D9AA5", weight=2.5, opacity=.62,
            tooltip=f"Job #{row['JobID']} · {escape(start)} → {escape(end)}",
        ).add_to(map_view)
        folium.CircleMarker(
            location=[lat, lon], radius=8,
            color=truck_color, weight=3, fill=True, fill_color=truck_color, fill_opacity=.95,
            tooltip=folium.Tooltip(
                _truck_tooltip(row, progress, truck_color), sticky=True, direction="top", opacity=.99,
                style="border:0;background:transparent;box-shadow:none;padding:0;",
            ),
        ).add_to(map_view)

    for city in sorted(mapped_cities):
        lon, lat = FINLAND_NODES[city]
        folium.CircleMarker(
            [lat, lon], radius=4, color="#ECEDE6", weight=1,
            fill=True, fill_color="#ECEDE6", fill_opacity=.9,
            tooltip=city,
        ).add_to(map_view)
    return map_view, plotted_jobs


@st.fragment(run_every="10m")
def render_fleet_map_panel(routes: pd.DataFrame, active_jobs: pd.DataFrame) -> None:
    """Render the map panel, refreshed automatically every ten minutes."""
    map_view, plotted_jobs = fleet_map(routes, active_jobs)
    st_folium(
        map_view, height=590, width=None, use_container_width=True,
        key="command_center_static_fleet_map", returned_objects=[],
    )
    st.markdown(
        '<div class="fi-map-legend"><span><i class="fi-legend-dot fi-legend-trucks"></i>Vehicles in transit</span>'
        '<span class="fi-map-disclaimer">Random illustrative points · not GPS · refresh or wait 10 minutes to move</span></div>',
        unsafe_allow_html=True,
    )
    if not plotted_jobs:
        st.caption("There are no in-transit trucks to plot right now. Route lanes still show the operating network.")
    st.caption("Hover a colored point for the truck, driver and route details.")

