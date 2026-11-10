"""Fleet Intelligence System: Streamlit entry point.

Run with:  streamlit run app.py
"""
import streamlit as st

from components.bootstrap import get_app_context
from components.health_panels import configuration_panel
from components.status_bar import render_top_bar
from components.theme import apply_theme
from utils.version import APP_VERSION, BUILD_PHASE

st.set_page_config(
    page_title="Fleet Intelligence",
    page_icon=":material/local_shipping:",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

ctx = get_app_context()

navigation = st.navigation(
    [
        st.Page("pages/command_center.py", title="Command Center", icon=":material/dashboard:", default=True),
        st.Page("pages/fleet.py", title="Fleet", icon=":material/local_shipping:"),
        st.Page("pages/drivers.py", title="Drivers", icon=":material/badge:"),
        st.Page("pages/operations.py", title="Operations", icon=":material/route:"),
        st.Page("pages/reports_system.py", title="Reports & System", icon=":material/monitoring:"),
    ]
)

render_top_bar(ctx)

with st.sidebar:
    st.caption(f"Version {APP_VERSION}, {BUILD_PHASE}")

if ctx.settings is None:
    st.error("The application is not configured. Copy .env.example to .env, fill in the database settings, then press Refresh.")
    configuration_panel(None, ctx.config_problems)
    st.stop()

navigation.run()
