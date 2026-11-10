"""Honest placeholders for sections that are built in later phases."""
from __future__ import annotations

from html import escape

import streamlit as st


def page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f'<h1 class="fi-title">{escape(title)}</h1><div class="fi-subtitle">{escape(subtitle)}</div>',
        unsafe_allow_html=True,
    )


def coming_in(phase: str, contents: str) -> None:
    st.markdown(
        f'<div class="fi-card"><div class="fi-card-title">Planned for {escape(phase)}</div>'
        f'<div class="fi-note">{escape(contents)}</div></div>',
        unsafe_allow_html=True,
    )
