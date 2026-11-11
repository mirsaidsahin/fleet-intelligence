import streamlit as st

from components.bootstrap import get_app_context
from components.entity_manager import entity_manager
from components.placeholders import page_header
from components.section_nav import section_nav

page_header("Operations", "Schedule and track jobs, routes, cargo and customers.")
ctx = get_app_context()
if not ctx.database:
    st.warning("Configure the database connection in Reports & System to manage operations.")
else:
    active = section_nav("operations_workspace", [
        ("Jobs", "DISPATCH", "Track work orders and current delivery status."),
        ("Cargo", "FREIGHT", "Manage loads, weight and declared value."),
        ("Routes", "NETWORK", "Maintain lanes, distances and route estimates."),
        ("Customers", "ACCOUNTS", "Keep shipper and customer records in order."),
    ])
    st.markdown(f'<div class="fi-section-label">{active} workspace</div>', unsafe_allow_html=True)
    if active == "Jobs":
        entity_manager(ctx.database, "jobs", "Job board")
    elif active == "Cargo":
        entity_manager(ctx.database, "cargos", "Cargo catalog")
    elif active == "Routes":
        entity_manager(ctx.database, "routes", "Route directory")
    else:
        entity_manager(ctx.database, "customers", "Customer directory")
