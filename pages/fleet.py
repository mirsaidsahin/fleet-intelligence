"""Workspace for editing trucks, brands, and garage records."""
import streamlit as st

from components.bootstrap import get_app_context
from components.entity_manager import entity_manager
from components.placeholders import page_header
from components.section_nav import section_nav

page_header("Fleet", "Manage trucks, manufacturer brands and garage locations.")
ctx = get_app_context()
if not ctx.database:
    st.warning("Configure the database connection in Reports & System to manage fleet records.")
else:
    active = section_nav("fleet_workspace", [
        ("Trucks", "VEHICLES", "Browse trucks, specifications and service status."),
        ("Brands", "MANUFACTURERS", "Maintain the makes represented in your fleet."),
        ("Garages", "LOCATIONS", "Review and manage your regional garage network."),
    ])
    st.markdown(f'<div class="fi-section-label">{active} workspace</div>', unsafe_allow_html=True)
    table, title = {
        "Trucks": ("trucks", "Truck catalog"),
        "Brands": ("brands", "Manufacturer brands"),
        "Garages": ("garages", "Garage locations"),
    }[active]
    entity_manager(ctx.database, table, title)
