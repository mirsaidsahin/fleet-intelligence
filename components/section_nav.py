"""Large, descriptive in-page navigation for entity management sections."""
from __future__ import annotations

import streamlit as st


def _select(state_key: str, value: str) -> None:
    st.session_state[state_key] = value


def section_nav(state_key: str, items: list[tuple[str, str, str]]) -> str:
    """Render sturdy selection cards as an alternative to tiny default tabs.

    Each tuple is (section name, short category, description). The selection is
    kept in session state, so reruns from forms don't reset the active section.
    """
    names = [item[0] for item in items]
    if st.session_state.get(state_key) not in names:
        st.session_state[state_key] = names[0]
    active = st.session_state[state_key]
    st.markdown('<div class="fi-section-label">Select workspace</div>', unsafe_allow_html=True)
    columns = st.columns(len(items), gap="small")
    for index, (column, item) in enumerate(zip(columns, items), start=1):
        name, category, description = item
        selected = name == active
        with column:
            st.markdown(
                f'<div class="fi-nav-card{" fi-active" if selected else ""}">'
                f'<div class="fi-nav-icon">{index:02d} &nbsp; / &nbsp; {category}</div>'
                f'<div class="fi-nav-title">{name}</div>'
                f'<div class="fi-nav-copy">{description}</div></div>',
                unsafe_allow_html=True,
            )
            st.button(
                "Workspace open" if selected else f"Open {name.lower()}",
                key=f"{state_key}_button_{index}",
                type="primary" if selected else "secondary",
                width="stretch",
                on_click=_select,
                args=(state_key, name),
            )
    return st.session_state[state_key]
