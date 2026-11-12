"""Honest placeholders for sections that are built in later phases."""
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


def coming_in(phase: str, contents: str) -> None:
    """Show a clearly labelled roadmap card for a feature not built yet."""
    # Keep placeholder copy safe because it is inserted into an HTML card.
    st.markdown(
        f'<div class="fi-card"><div class="fi-card-title">Planned for {escape(phase)}</div>'
        f'<div class="fi-note">{escape(contents)}</div></div>',
        unsafe_allow_html=True,
    )
