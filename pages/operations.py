import streamlit as st

from components.bootstrap import get_app_context
from components.entity_manager import entity_manager
from components.placeholders import page_header

page_header("Operations", "Schedule and track jobs, routes, cargo and customers.")
ctx = get_app_context()
if not ctx.database:
    st.warning("Configure the database connection in Reports & System to manage operations.")
else:
    jobs_tab, cargo_tab, route_tab, customer_tab = st.tabs(["Jobs", "Cargo", "Routes", "Customers"])
    with jobs_tab:
        entity_manager(ctx.database, "jobs", "Job board")
    with cargo_tab:
        entity_manager(ctx.database, "cargos", "Cargo catalog")
    with route_tab:
        entity_manager(ctx.database, "routes", "Route directory")
    with customer_tab:
        entity_manager(ctx.database, "customers", "Customer directory")
