"""Persistent in-page navigation for entity management sections."""
from __future__ import annotations

import streamlit as st


def section_nav(state_key: str, items: list[tuple[str, str, str]]) -> str:
    """Render a single segmented selector; tuples are name, category, description."""
    names = [item[0] for item in items]
    if st.session_state.get(state_key) not in names:
        st.session_state[state_key] = names[0]
    st.markdown('<div class="fi-section-label">Select workspace</div>', unsafe_allow_html=True)
    labels = {name: f"{index:02d}  /  {category}  ·  {name}" for index, (name, category, _) in enumerate(items, start=1)}
    active = st.segmented_control(
        "Select workspace",
        options=names,
        format_func=labels.__getitem__,
        key=state_key,
        selection_mode="single",
        label_visibility="collapsed",
        width="stretch",
    )
    active = active or names[0]
    description = next(description for name, _, description in items if name == active)
    st.caption(description)
    return active
