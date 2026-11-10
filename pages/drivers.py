import streamlit as st

from components.bootstrap import get_app_context
from components.entity_manager import entity_manager
from components.placeholders import page_header

page_header("Drivers", "Manage driver records, license classes and mentor links.")
ctx = get_app_context()
if not ctx.database:
    st.warning("Configure the database connection in Reports & System to manage drivers.")
else:
    entity_manager(ctx.database, "drivers", "Driver directory")
