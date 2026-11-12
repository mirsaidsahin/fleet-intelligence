"""Fleet Intelligence System: Streamlit entry point.

Run with:  streamlit run app.py
"""
import streamlit as st

from components.bootstrap import get_app_context
from components.health_panels import configuration_panel
from components.status_bar import render_top_bar
from components.theme import apply_theme
from components.welcome import show_welcome
from utils.version import APP_VERSION, BUILD_PHASE

# Set the shared browser title, icon, layout, and initial sidebar state.
st.set_page_config(
    page_title="Fleet Intelligence",
    page_icon=":material/local_shipping:",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Apply the project palette before any page content is rendered.
apply_theme()

# Load the cached database/settings context once for the current server process.
ctx = get_app_context()

# Register every top-level page and mark the command center as the landing page.
navigation = st.navigation(
    [
        st.Page("pages/command_center.py", title="Command Center", icon=":material/dashboard:", default=True),
        st.Page("pages/fleet.py", title="Fleet", icon=":material/local_shipping:"),
        st.Page("pages/drivers.py", title="Drivers", icon=":material/badge:"),
        st.Page("pages/operations.py", title="Operations", icon=":material/route:"),
        st.Page("pages/reports_system.py", title="Reports & System", icon=":material/monitoring:"),
    ]
)

# Keep database health visible while giving first-time users a short orientation.
render_top_bar(ctx)
show_welcome()

# Show the application version without crowding the main navigation.
with st.sidebar:
    st.caption(f"Version {APP_VERSION}, {BUILD_PHASE}")

# Stop before page execution when required database settings are invalid or missing.
if ctx.settings is None:
    st.error("The application is not configured. Copy .env.example to .env, fill in the database settings, then press Refresh.")
    configuration_panel(None, ctx.config_problems)
    st.stop()

# Dispatch control to the page selected in Streamlit's navigation widget.
navigation.run()
