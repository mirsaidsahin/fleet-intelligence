import streamlit as st

from components.bootstrap import get_app_context
from components.entity_manager import entity_manager
from components.placeholders import page_header

page_header("Fleet", "Manage trucks, manufacturer brands and garage locations.")
ctx = get_app_context()
if not ctx.database:
    st.warning("Configure the database connection in Reports & System to manage fleet records.")
else:
    truck_tab, brand_tab, garage_tab = st.tabs(["Trucks", "Brands", "Garages"])
    with truck_tab:
        entity_manager(ctx.database, "trucks", "Truck catalog")
    with brand_tab:
        entity_manager(ctx.database, "brands", "Manufacturer brands")
    with garage_tab:
        entity_manager(ctx.database, "garages", "Garage locations")
