"""A lightweight first-run welcome dialog, shown once per Streamlit session."""
from __future__ import annotations

import streamlit as st

SEEN_KEY = "fi_welcome_seen"


def _mark_seen() -> None:
    """Remember that this session has dismissed the welcome dialog."""
    st.session_state[SEEN_KEY] = True


@st.dialog("Welcome to Fleet Intelligence", icon=":material/local_shipping:", on_dismiss=_mark_seen)
def _welcome_dialog() -> None:
    st.subheader("Fleet and dispatch, at a glance")
    st.write("Monitor vehicle availability, review open jobs, check routes, and follow driver performance from one workspace.")
    st.info(
        "Illustrative content: map positions and truck/driver photos are for demonstration, not live tracking. "
        "This non-commercial school project uses brand names and logos only to identify vehicle makes; "
        "no ownership is claimed. Trademarks belong to their respective owners.",
        icon=":material/info:",
    )
    st.caption("Use the navigation on the left to explore the project. Database status and refresh time are shown at the top.")
    if st.button("Get started", type="primary", width="stretch", key="fi_welcome_dismiss"):
        _mark_seen()
        st.rerun()


def show_welcome() -> None:
    """Show the welcome dialog only until dismissed during this browser session."""
    if not st.session_state.get(SEEN_KEY, False):
        _welcome_dialog()
