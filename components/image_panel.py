"""Image preview for records with local image assets."""
from __future__ import annotations

import streamlit as st

from services.image_assets import brand_image, driver_image, truck_image


def _truck_preview(database, truck: dict, truck_id: int) -> None:
    """Show a truck with its current or assigned driver."""
    transit = database.fetch_one(
        "SELECT DriverID FROM jobs WHERE TruckID=:id AND Status='In Transit' ORDER BY StartDate DESC LIMIT 1",
        {"id": truck_id},
    )
    image_path = truck_image(truck_id, truck.get("BrandID"))
    driver_id = transit.get("DriverID") if transit else truck.get("AssignedDriverID")
    driver_path = driver_image(int(driver_id)) if driver_id else None
    driver = database.fetch_one(
        "SELECT CONCAT(FirstName, ' ', LastName) AS name FROM drivers WHERE DriverID=:id",
        {"id": driver_id},
    ) if driver_id else None
    vehicle_col, driver_col = st.columns([3, 1], vertical_alignment="center")
    with vehicle_col:
        if image_path:
            st.image(str(image_path), width=360)
            st.caption("Truck")
        else:
            st.caption("No truck image. See assets/README.md for supported filenames.")
    with driver_col:
        if driver_path:
            st.image(str(driver_path), width=128)
            st.caption("Current driver" if transit else "Assigned driver")
        else:
            st.caption("No driver photo")
        if driver:
            st.caption(driver["name"])


def image_panel(database, table: str, rows: list[dict], key_col: str) -> None:
    """Preview one record's local image."""
    selected_id = st.selectbox("Image preview", [int(row[key_col]) for row in rows], format_func=lambda x: f"#{x}", key=f"image_preview_{table}")
    if table == "trucks":
        selected = next(row for row in rows if int(row[key_col]) == selected_id)
        _truck_preview(database, selected, selected_id)
    else:
        image_path = driver_image(selected_id) if table == "drivers" else brand_image(selected_id)
        if image_path:
            st.image(str(image_path), width=144)
        else:
            st.caption("No local image. See assets/README.md for supported filenames.")
