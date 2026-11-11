"""A restrained night-shift operations interface: warm steel, paper white and safety ochre."""
from __future__ import annotations

import streamlit as st


_CSS = """
<style>
:root {
  --fi-bg:#121514;
  --fi-panel:#191D1B;
  --fi-raised:#212724;
  --fi-line:#333A36;
  --fi-text:#ECEDE6;
  --fi-muted:#A8AFA6;
  --fi-disabled:#6F766D;
  --fi-ochre:#D69A4A;
  --fi-rust:#C77658;
  --fi-sage:#8FA37A;
  --fi-blue:#7D9AA5;
  --fi-space-1:4px;
  --fi-space-2:8px;
  --fi-space-3:12px;
  --fi-space-4:16px;
  --fi-space-5:24px;
  --fi-space-6:32px;
  --fi-radius-sm:4px;
  --fi-radius-card:6px;
  --fi-radius-dialog:8px;
  --fi-font:"Bahnschrift","Aptos","Segoe UI Variable","Segoe UI",Arial,sans-serif;
  --fi-mono:"Cascadia Code","Consolas",monospace;
}

html, body, [data-testid="stAppViewContainer"] { background:var(--fi-bg); }
.stApp { background:var(--fi-bg); color:var(--fi-text); font-family:var(--fi-font); }
.stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stMetricLabel"] {
  font-family:var(--fi-font) !important;
}
.stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button { font-size:14px; line-height:22px; }
.block-container { max-width:1540px; padding:.8rem 2rem 3.25rem; }
[data-testid="stHeader"] { display:none !important; height:0 !important; min-height:0 !important; }
hr, .fi-rule { display:none !important; }
[data-testid="stSidebar"] { background:var(--fi-panel); border-right:1px solid var(--fi-line); }
[data-testid="stSidebarNav"] { padding:.6rem .45rem; }
[data-testid="stSidebarNav"] a { min-height:2.75rem; margin:.15rem 0; border-radius:var(--fi-radius-sm); color:var(--fi-text); }
[data-testid="stSidebarNav"] a:hover { background:var(--fi-raised); color:#FFF; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background:var(--fi-raised); border-left:3px solid var(--fi-ochre); color:#FFF; }
footer { visibility:hidden; }

.stApp h1, .stApp h2, .stApp h3 { color:var(--fi-text); font-family:var(--fi-font); font-weight:650; letter-spacing:-.02em; }
.stApp h1 { font-size:22px; line-height:28px; }
.stApp h2 { font-size:18px; line-height:24px; }
.stApp h3 { font-size:16px; line-height:22px; }
.fi-title { margin:0; color:var(--fi-text); font-size:22px; line-height:28px; font-weight:700; letter-spacing:-.025em; }
.fi-subtitle { margin:var(--fi-space-2) 0 var(--fi-space-5); color:var(--fi-muted); font-size:14px; line-height:22px; }
.fi-section-label { display:flex; align-items:center; gap:.65rem; margin:.55rem 0 .65rem; color:var(--fi-muted); font-size:12px; line-height:18px; font-weight:700; letter-spacing:.13em; text-transform:uppercase; }
.fi-section-label:before { content:""; width:1.5rem; height:2px; background:var(--fi-ochre); }

.fi-wordmark { display:flex; align-items:center; gap:.7rem; }
.fi-bar { width:4px; height:2.15rem; background:var(--fi-ochre); flex:none; }
.fi-wm-title { color:var(--fi-text); font-family:var(--fi-font); font-size:18px; line-height:24px; font-weight:700; letter-spacing:.01em; }
.fi-wm-sub { margin-top:.18rem; color:var(--fi-muted); font-size:12px; line-height:18px; }
.fi-pill { display:flex; align-items:center; gap:.65rem; padding:.5rem .75rem; border:1px solid var(--fi-line); border-radius:5px; background:var(--fi-panel); }
.fi-dot { width:.56rem; height:.56rem; border-radius:50%; flex:none; }
.fi-ok .fi-dot { background:var(--fi-sage); }
.fi-warn .fi-dot { background:var(--fi-ochre); }
.fi-bad .fi-dot { background:var(--fi-rust); }
.fi-bad { border-color:var(--fi-rust); }
.fi-pill-title { color:var(--fi-text); font-size:14px; font-weight:650; line-height:22px; }
.fi-pill-sub { color:var(--fi-muted); font-size:12px; line-height:18px; }
.fi-stamp-label { color:var(--fi-muted); font-size:12px; line-height:18px; }
.fi-stamp-value { color:var(--fi-text); font-family:var(--fi-mono); font-size:12px; line-height:18px; font-variant-numeric:tabular-nums; }
.fi-rule { height:1px; border:0; background:var(--fi-line); margin:.8rem 0 1.25rem; }

.fi-hero { position:relative; margin:var(--fi-space-2) 0 var(--fi-space-4); padding:var(--fi-space-5); border:1px solid var(--fi-line); border-left:4px solid var(--fi-ochre); border-radius:var(--fi-radius-card); background:var(--fi-panel); }
.fi-hero:after { content:none; }
.fi-eyebrow { color:var(--fi-ochre); font-family:var(--fi-mono); font-size:12px; line-height:18px; letter-spacing:.08em; }
.fi-hero-title { margin-top:var(--fi-space-2); color:var(--fi-text); font-size:28px; line-height:32px; font-weight:700; letter-spacing:-.035em; }
.fi-hero-sub { margin-top:var(--fi-space-2); color:var(--fi-muted); font-size:14px; line-height:22px; }

[data-testid="stMetric"] { min-height:106px; padding:var(--fi-space-3); border:1px solid var(--fi-line); border-top:2px solid var(--fi-raised); border-radius:var(--fi-radius-card); background:var(--fi-panel); box-shadow:none; }
[data-testid="stMetricLabel"] { color:var(--fi-muted); font-size:12px; line-height:18px; letter-spacing:.025em; }
[data-testid="stMetricValue"] { color:var(--fi-text); font-family:var(--fi-mono) !important; font-size:28px; line-height:32px; font-weight:600; font-variant-numeric:tabular-nums; letter-spacing:-.04em; }
[data-testid="stMetricDelta"] { font-size:.75rem; }
[data-testid="stProgress"] > div { background:#353B37; border-radius:2px; }
[data-testid="stProgress"] > div > div { background:var(--fi-ochre); border-radius:2px; }

.stButton > button { min-height:2.45rem; border:1px solid var(--fi-line); border-radius:var(--fi-radius-sm); background:var(--fi-raised); color:var(--fi-text); font-weight:600; box-shadow:none; transition:background .12s,border-color .12s; }
.stButton > button:hover { border-color:var(--fi-ochre); background:#2B332E; color:#FFF; transform:none; }
.stButton > button[kind="primary"] { border-color:var(--fi-ochre); background:var(--fi-ochre); color:#211B12; font-weight:700; }
.stButton > button[kind="primary"]:hover { border-color:#E2B36F; background:#E2B36F; color:#211B12; }
.stDownloadButton > button { border-color:var(--fi-blue); }

[data-testid="stTabs"] [role="tablist"] { gap:.35rem; border-bottom:1px solid var(--fi-line); }
[data-testid="stTabs"] [role="tab"] { min-height:2.8rem; padding:.55rem 1rem; border:1px solid transparent; border-bottom:0; border-radius:var(--fi-radius-sm) var(--fi-radius-sm) 0 0; background:transparent; color:var(--fi-muted); font-size:14px; line-height:22px; font-weight:650; }
[data-testid="stTabs"] [role="tab"]:hover { background:var(--fi-raised); color:var(--fi-text); }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { border-color:var(--fi-line); border-top:2px solid var(--fi-ochre); background:var(--fi-panel); color:var(--fi-text); }

.fi-card { height:100%; padding:var(--fi-space-4); border:1px solid var(--fi-line); border-radius:var(--fi-radius-card); background:var(--fi-panel); }
.fi-card-title { margin-bottom:var(--fi-space-3); color:var(--fi-text); font-size:14px; line-height:22px; font-weight:650; }
.fi-kv { display:flex; justify-content:space-between; gap:1rem; padding:.38rem 0; border-bottom:1px solid var(--fi-line); font-size:14px; line-height:22px; }
.fi-kv:last-child { border-bottom:0; }
.fi-kv span:first-child,.fi-note { color:var(--fi-muted); }
.fi-kv span:last-child { color:var(--fi-text); text-align:right; font-family:var(--fi-mono); font-variant-numeric:tabular-nums; }
.fi-note { font-size:14px; line-height:22px; }
.fi-ok-text { color:var(--fi-sage); }
.fi-warn-text { color:var(--fi-ochre); }
.fi-bad-text { color:var(--fi-rust); }

.fi-nav-card { min-height:104px; margin:.25rem 0 .65rem; padding:.8rem .85rem .45rem; border:1px solid var(--fi-line); border-radius:var(--fi-radius-card); background:var(--fi-panel); }
.fi-nav-card.fi-active { border-color:var(--fi-ochre); border-top:3px solid var(--fi-ochre); padding-top:calc(.8rem - 2px); background:var(--fi-raised); box-shadow:none; }
.fi-nav-icon { color:var(--fi-ochre); font-family:var(--fi-mono); font-size:.67rem; letter-spacing:.04em; }
.fi-nav-title { margin:.25rem 0 .15rem; color:var(--fi-text); font-size:14px; line-height:22px; font-weight:700; }
.fi-nav-copy { min-height:2em; color:var(--fi-muted); font-size:.73rem; line-height:1.35; }

[data-testid="stSegmentedControl"] { border:1px solid var(--fi-line); border-radius:var(--fi-radius-card); background:var(--fi-panel); padding:var(--fi-space-1); }
[data-testid="stSegmentedControl"] button { min-height:42px; border-radius:var(--fi-radius-sm); font-size:14px; line-height:22px; }
[data-testid="stSegmentedControl"] button[aria-pressed="true"] { background:var(--fi-raised); color:var(--fi-text); box-shadow:inset 0 -2px 0 var(--fi-ochre); }

.fi-attention { margin:var(--fi-space-2) 0 var(--fi-space-5); padding:var(--fi-space-4); border:1px solid var(--fi-line); border-radius:var(--fi-radius-card); background:var(--fi-panel); }
.fi-attention-head { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:.5rem; }
.fi-attention-title { color:var(--fi-text); font-size:14px; line-height:22px; font-weight:700; }
.fi-attention-count { color:var(--fi-ochre); font-family:var(--fi-mono); font-size:.71rem; font-weight:700; }
.fi-alert { margin:.35rem 0; padding:.6rem .75rem; border:1px solid var(--fi-line); border-left:3px solid var(--fi-rust); border-radius:var(--fi-radius-sm); background:var(--fi-raised); }
.fi-alert-title { color:var(--fi-text); font-size:14px; line-height:22px; font-weight:700; }
.fi-alert-detail { margin-top:.18rem; color:var(--fi-muted); font-size:12px; line-height:18px; }

[data-testid="stDataFrame"] { border:1px solid var(--fi-line); border-radius:4px; overflow:hidden; }
[data-testid="stPlotlyChart"] { border:1px solid var(--fi-line); border-radius:5px; background:var(--fi-panel); padding:.15rem; }
[data-testid="stExpander"] { border:1px solid var(--fi-line); border-radius:4px; background:var(--fi-panel); }
[data-testid="stExpander"] summary:hover { color:var(--fi-ochre); }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stDateInput"] input,
[data-testid="stSelectbox"] [data-baseweb="select"] > div, [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
[data-testid="stTextArea"] textarea { border-color:var(--fi-line); border-radius:var(--fi-radius-sm); background:var(--fi-raised); }
[data-testid="stFileUploader"] section { border:1px dashed var(--fi-muted); border-radius:var(--fi-radius-sm); background:var(--fi-panel); }
[data-testid="stForm"] { padding:var(--fi-space-4); border:1px solid var(--fi-line); border-radius:var(--fi-radius-card); background:var(--fi-panel); }
[data-testid="stRadio"] [role="radiogroup"] { gap:.6rem; }
div[data-testid="stAlert"] { border-radius:var(--fi-radius-sm); }
[data-testid="stCaptionContainer"] { color:var(--fi-muted); }
a { color:var(--fi-ochre); }
a:hover { color:#E2B36F; }
.stCaption, [data-testid="stCaptionContainer"] p { font-size:12px; line-height:18px; }
:is(button, a, input, textarea, select, [tabindex]):focus-visible { outline:2px solid var(--fi-ochre) !important; outline-offset:2px !important; }
:disabled, [aria-disabled="true"] { color:var(--fi-disabled) !important; }

/* A compact layout for the report/system workspace and short screens. */
@media (max-width: 1100px) {
  .block-container { padding-top:1rem; }
  .fi-title { font-size:22px; }
  .fi-hero-title { font-size:24px; line-height:30px; }
}
@media (max-width: 700px) {
  .block-container { padding:.85rem .75rem 2rem; }
  .fi-title { font-size:22px; }
  .fi-subtitle { margin-bottom:1rem; }
  [data-testid="stMetric"] { min-height:88px; padding:.65rem; }
  [data-testid="stMetricValue"] { font-size:1.35rem; }
}

.fi-map-legend { display:flex; flex-wrap:wrap; align-items:center; gap:.65rem 1.25rem; padding:.6rem .2rem .2rem; color:var(--fi-muted); font-size:.75rem; }
.fi-map-legend span { display:inline-flex; align-items:center; gap:.4rem; }
.fi-legend-dot { display:inline-block; width:.65rem; height:.65rem; border:1px solid var(--fi-bg); border-radius:50%; background:var(--fi-blue); }
.fi-legend-trucks { background:linear-gradient(135deg,var(--fi-blue),var(--fi-sage),var(--fi-ochre),var(--fi-rust)); }
.fi-legend-line { display:inline-block; width:1rem; border-top:3px solid var(--fi-ochre); }
.fi-map-disclaimer { color:#B6AA96; }
.fi-map-selection { display:flex; flex-wrap:wrap; gap:.35rem .8rem; align-items:center; margin:.25rem 0; padding:.65rem .8rem; border:1px solid var(--fi-ochre); border-radius:var(--fi-radius-sm); background:var(--fi-raised); }
.fi-map-selection strong { color:var(--fi-ochre); }
.fi-map-selection span { color:var(--fi-muted); font-size:.82rem; }

@media (max-width: 900px) { .block-container { padding-left:1rem; padding-right:1rem; } .fi-hero:after { display:none; } }
</style>
"""


def apply_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
