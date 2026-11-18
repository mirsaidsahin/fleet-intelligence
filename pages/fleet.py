"""Workspace for editing trucks, brands, garages, and driver records."""
import streamlit as st

from components.bootstrap import get_app_context
from components.entity_manager import entity_manager
from components.ui import page_header, section_nav

page_header("Fleet", "Manage trucks, manufacturer brands, garage locations and drivers.")
ctx = get_app_context()
if not ctx.database:
    st.warning("Configure the database connection in System to manage fleet records.")
else:
    active = section_nav("fleet_workspace", [
        ("Trucks", "VEHICLES", "Browse trucks, specifications and service status."),
        ("Brands", "MANUFACTURERS", "Maintain the makes represented in your fleet."),
        ("Garages", "LOCATIONS", "Review and manage your regional garage network."),
        ("Drivers", "PEOPLE", "Manage driver records, license classes and mentor links."),
    ])
    st.markdown(f'<div class="fi-section-label">{active} workspace</div>', unsafe_allow_html=True)
    table, title = {
        "Trucks": ("trucks", "Truck catalog"),
        "Brands": ("brands", "Manufacturer brands"),
        "Garages": ("garages", "Garage locations"),
        "Drivers": ("drivers", "Driver directory"),
    }[active]
    entity_manager(ctx.database, table, title)
