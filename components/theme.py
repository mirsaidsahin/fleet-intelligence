"""A restrained night-shift operations interface: warm steel, paper white and safety ochre."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

# Shared design tokens and component styling live beside this module as plain CSS.
_CSS = Path(__file__).with_name("theme.css").read_text(encoding="utf-8")


def apply_theme() -> None:
    """Inject the shared visual theme into the current Streamlit page."""
    st.markdown(_CSS, unsafe_allow_html=True)
