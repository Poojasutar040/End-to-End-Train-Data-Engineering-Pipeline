"""Main Streamlit application entry point with multi-page navigation."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from dashboard.data_loader import get_cached_kpis, get_mysql_status
from dashboard.styles import apply_custom_styles

st.set_page_config(
    page_title="Smart Railway Analytics & Prediction System",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_styles()


pages = [
    st.Page("pages/1_Home_Dashboard.py", title="Home Dashboard", icon="🏠", default=True),
    st.Page("pages/2_Train_Search.py", title="Train Search", icon="🔎"),
    st.Page("pages/3_Route_Analysis.py", title="Train Route Analysis", icon="🗺️"),
    st.Page("pages/4_Duration_Prediction.py", title="Journey Duration Prediction", icon="🤖"),
    st.Page("pages/5_Data_Analytics.py", title="Data Analytics", icon="📊"),

    # Hidden for now — files are preserved
    # st.Page("pages/6_Reports.py", title="Reports", icon="📄"),
    # st.Page("pages/7_About_Project.py", title="About Project", icon="🎓"),
]

navigation = st.navigation(pages)
navigation.run()