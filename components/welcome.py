"""A lightweight first-run welcome dialog, shown once per Streamlit session."""
from __future__ import annotations

import streamlit as st

SEEN_KEY = "fi_welcome_seen"


def _mark_seen() -> None:
    st.session_state[SEEN_KEY] = True


@st.dialog("Welcome to Fleet Intelligence", icon=":material/local_shipping:", on_dismiss=_mark_seen)
def _welcome_dialog() -> None:
    st.write("Your operations overview for fleet status, dispatch work, drivers, routes, and reports.")
    st.info("Truck positions on the map are illustrative points along routes, not live GPS locations.", icon=":material/info:")
    st.caption("Use the navigation on the left to explore the project. Database status and refresh time are shown at the top.")
    if st.button("Get started", type="primary", width="stretch", key="fi_welcome_dismiss"):
        _mark_seen()
        st.rerun()


def show_welcome() -> None:
    """Show the welcome dialog only until dismissed during this browser session."""
    if not st.session_state.get(SEEN_KEY, False):
        _welcome_dialog()
