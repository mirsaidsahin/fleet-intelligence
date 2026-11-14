"""Shared page heading used by every top-level page."""
from __future__ import annotations

from html import escape

import streamlit as st


def page_header(title: str, subtitle: str) -> None:
    """Render a consistent page title and supporting description."""
    # Escape page copy before inserting it into the shared HTML heading.
    st.markdown(
        f'<h1 class="fi-title">{escape(title)}</h1><div class="fi-subtitle">{escape(subtitle)}</div>',
        unsafe_allow_html=True,
    )
