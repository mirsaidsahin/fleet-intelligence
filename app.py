"""Fleet Intelligence System: Streamlit entry point.

Run with:  streamlit run app.py
"""
import streamlit as st

from components.bootstrap import get_app_context
from components.status_bar import render_top_bar
from components.theme import apply_theme
from utils.version import APP_VERSION

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
        st.Page("pages/operations.py", title="Operations", icon=":material/route:"),
        st.Page("pages/system.py", title="System", icon=":material/monitoring:"),
    ]
)

# Keep database health visible at the top of every page.
render_top_bar(ctx)

# Show the application version and demonstration disclaimer without crowding the navigation.
with st.sidebar:
    st.caption(f"Version {APP_VERSION}")
    st.caption(
        "Map positions are illustrative, not live tracking. Brand logos are for demonstration only; "
        "trademarks belong to their respective owners."
    )

# Stop before page execution when required database settings are invalid or missing.
if ctx.settings is None:
    st.error("The application is not configured. Copy .env.example to .env, fill in the database settings, then press Refresh.")
    for problem in ctx.config_problems:
        st.error(problem)
    st.stop()

# Dispatch control to the page selected in Streamlit's navigation widget.
navigation.run()
