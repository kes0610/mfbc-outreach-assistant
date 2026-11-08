"""Shared branded styling for every page — an editorial, black-and-white-
photography-and-red-accent look pulled from a full read of MFBC's own
Instagram (bold circular wordmark, all-caps display headers, a confident
red used across their convention/sponsor graphics), instead of Streamlit's
generic defaults or a generic "cozy fall" palette."""

import streamlit as st

CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,500;0,600;0,700;1,500&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
h1, h2, h3, .mfbc-display {
    font-family: 'Fraunces', serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
    color: #1A1A1A !important;
}
h2, h3 {
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-size: 1.1rem !important;
}
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #FFFFFF 0%, #FAF8F4 400px);
}
[data-testid="stSidebar"] {
    background-color: #EDEAE2;
    border-right: 1px solid #D8D3C6;
}
[data-testid="stSidebar"] a, [data-testid="stSidebar"] span {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 0.85rem;
    letter-spacing: 0.03em;
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
    background: #1A1A1A;
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    font-size: 14px;
    letter-spacing: 0.02em;
    border: 3px solid #A61C33;
}
.mfbc-header-title {
    font-family: 'Fraunces', serif;
    font-weight: 600;
    font-size: 2rem;
    color: #1A1A1A;
    line-height: 1.1;
    margin: 0;
}
.mfbc-header-subtitle {
    font-family: 'Inter', sans-serif;
    color: #6B6B6B;
    font-size: 0.95rem;
    margin-top: 2px;
}

/* Metric cards */
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #E5E1D8;
    border-top: 3px solid #A61C33;
    border-radius: 4px;
    padding: 14px 16px 10px 16px;
}
[data-testid="stMetricLabel"] {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.04em;
    color: #6B6B6B;
}
[data-testid="stMetricValue"] {
    font-family: 'Fraunces', serif;
    color: #A61C33;
}

/* Buttons */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    border-radius: 2px;
    border: 1px solid #A61C33;
    font-weight: 700;
    font-family: 'Inter', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    font-size: 0.85rem;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    background-color: #A61C33;
    border-color: #A61C33;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
    background-color: #7E1427;
    border-color: #7E1427;
}

/* Tabs */
button[data-baseweb="tab"] {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 0.8rem;
    letter-spacing: 0.03em;
}
[data-baseweb="tab-highlight"] {
    background-color: #A61C33 !important;
}

hr {
    border-color: #D8D3C6 !important;
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
