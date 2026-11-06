"""Shared branded styling for every page — warm editorial look pulled from
MFBC's own Instagram (bold circular wordmark, autumnal palette), instead of
Streamlit's generic defaults."""

import streamlit as st

CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,500;0,600;0,700;1,500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
h1, h2, h3, .mfbc-display {
    font-family: 'Fraunces', serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
    color: #2B2420 !important;
}
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #F8F4EA 0%, #F6F1E7 400px);
}
[data-testid="stSidebar"] {
    background-color: #ECE0C9;
    border-right: 1px solid #DCCBA3;
}
[data-testid="stSidebar"] a, [data-testid="stSidebar"] span {
    font-family: 'Inter', sans-serif;
    font-weight: 500;
}

/* Branded header badge + wordmark */
.mfbc-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 4px;
}
.mfbc-badge {
    flex-shrink: 0;
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: #2B2420;
    color: #F6F1E7;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    font-size: 14px;
    letter-spacing: 0.02em;
    border: 3px solid #A8502E;
}
.mfbc-header-title {
    font-family: 'Fraunces', serif;
    font-weight: 600;
    font-size: 2rem;
    color: #2B2420;
    line-height: 1.1;
    margin: 0;
}
.mfbc-header-subtitle {
    font-family: 'Inter', sans-serif;
    color: #6B5D4F;
    font-size: 0.95rem;
    margin-top: 2px;
}

/* Metric cards */
[data-testid="stMetric"] {
    background-color: #FFFDF8;
    border: 1px solid #E3D5B4;
    border-radius: 10px;
    padding: 14px 16px 10px 16px;
}
[data-testid="stMetricLabel"] {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    color: #6B5D4F;
}
[data-testid="stMetricValue"] {
    font-family: 'Fraunces', serif;
    color: #A8502E;
}

/* Buttons */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    border-radius: 8px;
    border: 1px solid #A8502E;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    background-color: #A8502E;
    border-color: #A8502E;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
    background-color: #8A3F22;
    border-color: #8A3F22;
}

/* Tabs */
button[data-baseweb="tab"] {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
}

hr {
    border-color: #DCCBA3 !important;
}
</style>
"""


def inject_global_css():
    st.html(CSS)


def page_header(title: str, subtitle: str = ""):
    subtitle_html = f'<div class="mfbc-header-subtitle">{subtitle}</div>' if subtitle else ""
    st.html(
        f'<div class="mfbc-header"><div class="mfbc-badge">MFBC</div>'
        f'<div><p class="mfbc-header-title">{title}</p>{subtitle_html}</div></div>'
    )
