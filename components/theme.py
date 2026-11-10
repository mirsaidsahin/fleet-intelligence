"""Industrial dark theme: charcoal and graphite surfaces, amber accent, red only for faults."""
from __future__ import annotations

import streamlit as st

_CSS = """
<style>
:root {
  --fi-bg:#17191C; --fi-surface:#20242A; --fi-line:#333941;
  --fi-text:#E8E9EB; --fi-muted:#9097A1;
  --fi-amber:#F2A33A; --fi-red:#E5484D; --fi-green:#4FA66B;
  --fi-font:"Bahnschrift","Segoe UI",system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif;
}
.block-container { padding-top: 1.4rem; max-width: 1480px; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: var(--fi-surface); border-right: 1px solid var(--fi-line); }
footer { visibility: hidden; }
.stApp h1, .stApp h2, .stApp h3 { font-family: var(--fi-font); font-weight: 600; letter-spacing: .01em; }
.stButton > button { border: 1px solid var(--fi-line); background: var(--fi-surface); border-radius: 6px; }
.stButton > button:hover { border-color: var(--fi-amber); color: var(--fi-amber); }

.fi-wordmark { display:flex; align-items:center; gap:.7rem; }
.fi-bar { width:5px; height:2.3rem; background:var(--fi-amber); border-radius:2px; flex:none; }
.fi-wm-title { font-family:var(--fi-font); font-size:1.3rem; font-weight:700; line-height:1.1; }
.fi-wm-sub { color:var(--fi-muted); font-size:.8rem; }

.fi-pill { display:flex; align-items:center; gap:.65rem; padding:.45rem .85rem;
  border:1px solid var(--fi-line); border-radius:6px; background:var(--fi-surface); }
.fi-dot { width:.6rem; height:.6rem; border-radius:50%; flex:none; }
.fi-ok .fi-dot { background:var(--fi-green); }
.fi-warn .fi-dot { background:var(--fi-amber); }
.fi-bad .fi-dot { background:var(--fi-red); }
.fi-bad { border-color:var(--fi-red); }
.fi-pill-title { font-weight:600; font-size:.95rem; line-height:1.2; }
.fi-pill-sub { color:var(--fi-muted); font-size:.78rem; line-height:1.25; }

.fi-stamp-label { color:var(--fi-muted); font-size:.78rem; }
.fi-stamp-value { font-size:.95rem; font-variant-numeric:tabular-nums; }
.fi-rule { border:none; border-top:1px solid var(--fi-line); margin:.7rem 0 1.3rem; }

.fi-title { font-family:var(--fi-font); font-size:1.9rem; font-weight:700; margin:0; }
.fi-subtitle { color:var(--fi-muted); margin:.2rem 0 1.3rem; }

.fi-card { background:var(--fi-surface); border:1px solid var(--fi-line); border-radius:8px;
  padding:1rem 1.1rem; height:100%; }
.fi-card-title { font-weight:600; margin-bottom:.6rem; }
.fi-kv { display:flex; justify-content:space-between; gap:1rem; padding:.3rem 0;
  border-bottom:1px solid var(--fi-line); font-size:.9rem; }
.fi-kv:last-child { border-bottom:none; }
.fi-kv span:first-child { color:var(--fi-muted); }
.fi-kv span:last-child { text-align:right; font-variant-numeric:tabular-nums; }
.fi-ok-text { color:var(--fi-green); }
.fi-warn-text { color:var(--fi-amber); }
.fi-bad-text { color:var(--fi-red); }
.fi-note { color:var(--fi-muted); font-size:.9rem; line-height:1.5; }
.fi-hero { position:relative; overflow:hidden; margin:.35rem 0 1.15rem; padding:1.15rem 1.3rem;
  border:1px solid #343b43; border-left:4px solid var(--fi-amber); border-radius:9px;
  background:linear-gradient(105deg,rgba(242,163,58,.12),rgba(32,36,42,.96) 42%,#20242A); }
.fi-eyebrow { color:var(--fi-amber); font-size:.72rem; font-weight:700; letter-spacing:.14em; }
.fi-hero-title { margin-top:.3rem; font-family:var(--fi-font); font-size:1.8rem; font-weight:700; }
.fi-hero-sub { margin-top:.15rem; color:var(--fi-muted); font-size:.9rem; }
.fi-alert { margin:.55rem 0; padding:.65rem .8rem; border:1px solid rgba(229,72,77,.35);
  border-left:3px solid var(--fi-red); border-radius:6px; background:rgba(229,72,77,.07); }
.fi-alert-title { font-weight:700; font-size:.9rem; }
.fi-alert-detail { color:var(--fi-muted); margin-top:.2rem; font-size:.8rem; }
[data-testid="stMetric"] { min-height:104px; padding:.75rem .9rem; border:1px solid var(--fi-line);
  border-radius:8px; background:linear-gradient(145deg,#242930,#1d2025); }
[data-testid="stMetricLabel"] { color:var(--fi-muted); }
[data-testid="stMetricValue"] { font-variant-numeric:tabular-nums; }
[data-testid="stTabs"] [role="tab"] { font-weight:600; }
</style>
"""


def apply_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
