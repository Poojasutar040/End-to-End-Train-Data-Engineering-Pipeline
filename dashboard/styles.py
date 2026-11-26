

"""Custom CSS styling for the Smart Railway Analytics Streamlit application."""

from __future__ import annotations

import streamlit as st

CUSTOM_CSS = """
<style>
    /* Global layout */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }

    /* Main application background and text */
    .stApp {
        background-color: #f4f7fc;
        color: #172554;
    }

    /* Hero banner */
    .hero-banner {
        background: linear-gradient(135deg, #0b1f3a 0%, #173b70 55%, #087eaa 100%);
        padding: 1.8rem 2rem;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.14);
    }

    .hero-banner h1 {
        margin: 0;
        font-size: 1.9rem;
        font-weight: 750;
        letter-spacing: -0.02em;
        color: #ffffff;
    }

    .hero-banner p {
        margin: 0.5rem 0 0;
        font-size: 1rem;
        color: #dbeafe;
    }

    /* KPI cards */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #dce5f1;
        border-left: 5px solid #2563eb;
        border-radius: 14px;
        padding: 1.15rem 1.25rem;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
        margin-bottom: 0.8rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.10);
    }

    .kpi-label {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 0.35rem;
    }

    .kpi-value {
        font-size: 1.8rem;
        font-weight: 750;
        color: #102a56;
        line-height: 1.2;
    }

    .kpi-sub {
        font-size: 0.82rem;
        color: #087eaa;
        margin-top: 0.35rem;
    }

    /* Information box */
    .info-card {
        background: #eff8ff;
        border: 1px solid #bae0f7;
        border-left: 4px solid #0284c7;
        border-radius: 12px;
        padding: 1rem 1.15rem;
        color: #164e73;
        margin-bottom: 1rem;
    }

    /* Prediction result */
    .prediction-result {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 1px solid #86efac;
        border-radius: 14px;
        padding: 1.3rem 1.5rem;
        color: #064e3b;
        margin: 1rem 0;
    }

    .prediction-result h2 {
        margin: 0;
        font-size: 1.9rem;
        color: #065f46;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #dce5f1;
    }

    section[data-testid="stSidebar"] > div {
        background: #ffffff !important;
    }

    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: #102a56 !important;
    }

    /* Sidebar navigation */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
        color: #243b5a !important;
        border-radius: 9px;
        margin: 3px 0;
    }

    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] p {
        color: #243b5a !important;
        opacity: 1 !important;
        font-weight: 500;
    }

    /* Selected navigation item */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
        background: #e7f0ff !important;
        font-weight: 700 !important;
    }

    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] p {
        color: #1d4ed8 !important;
        font-weight: 700 !important;
    }

    /* Navigation hover */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {
        background: #f0f5fc !important;
    }

    /* Buttons */
    .stButton > button {
        background: #174a8b;
        color: #ffffff;
        border: 1px solid #174a8b;
        border-radius: 9px;
        font-weight: 600;
        padding: 0.45rem 1rem;
        transition: background 0.2s ease;
    }

    .stButton > button:hover {
        background: #0b2f60;
        border-color: #0b2f60;
        color: #ffffff;
    }

    /* Input fields */
    .stTextInput input,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px;
    }

    /* Dataframes and tables */
    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
        border: 1px solid #dce5f1;
        border-radius: 10px;
        overflow: hidden;
    }

    /* Section headings */
    h1, h2, h3 {
        color: #102a56;
    }

    /* Horizontal separator */
    hr {
        border-color: #dce5f1;
    }
</style>
"""


def apply_custom_styles() -> None:
    """Inject custom CSS into the active Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_hero(title: str, subtitle: str) -> None:
    """Render a consistent gradient page header."""
    st.markdown(
        f"""
        <div class="hero-banner">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, subtext: str = "") -> None:
    """Render a styled KPI metric card."""
    sub_html = f'<div class="kpi-sub">{subtext}</div>' if subtext else ""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
