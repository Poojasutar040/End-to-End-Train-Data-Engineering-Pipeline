"""Page 7: About Project — MCA Major Project overview, architecture, and diagrams."""

from __future__ import annotations

import streamlit as st

from dashboard.styles import render_hero
from utils.config import PATHS

render_hero(
    "About This MCA Major Project",
    "Smart Railway Analytics and Train Journey Prediction System — Architecture, Methodology & Documentation",
)

st.markdown(
    """
    ### Abstract
    The **Smart Railway Analytics and Train Journey Prediction System** transforms raw Indian railway
    schedule data (186,074 timetable records across 11,113 trains and 8,147 stations) into a modular
    **Data Engineering, Machine Learning, MySQL, and Web Analytics** platform.

    ### Key Architectural Components
    1. **Ingestion & Validation (`ingestion/`):** Loads raw timetable CSVs and enforces schema integrity.
    2. **Cleaning & Transformation (`preprocessing/`):** Removes duplicates, normalizes station naming
       inconsistencies, sorts stops strictly by `(Train_No, SN)`, handles midnight wrap-arounds, and
       computes segment distances, halt durations, and full-route journey times.
    3. **Relational Persistence (`database/`):** Normalized MySQL 8.0 schema (`stations`, `trains`,
       `train_schedules`, `train_routes`, `prediction_history`) using parameterized SQL and `.env` credentials.
    4. **Analytics Engine (`analytics/`):** KPI computation, train/station/Origin-Destination search,
       and route comparisons.
    5. **Machine Learning (`models/`):** Compares **Linear Regression**, **Decision Tree**, and
       **Random Forest** regressors using **MAE, RMSE, and R²** to predict scheduled leg duration.
    6. **Interactive Frontend (`dashboard/`):** Multi-page **Streamlit + Plotly** web application with custom CSS.
    """
)

st.divider()
st.subheader("System Architecture, Data Flow & ER Diagrams")

diagram_files = [
    ("System Architecture", PATHS.diagrams_dir / "system_architecture.png"),
    ("Data Flow Diagram (DFD)", PATHS.diagrams_dir / "data_flow_diagram.png"),
    ("Entity-Relationship (ER) Diagram", PATHS.diagrams_dir / "er_diagram.png"),
]

cols = st.columns(3)
for col, (caption, path) in zip(cols, diagram_files):
    with col:
        if path.exists():
            st.image(str(path), caption=caption, use_container_width=True)
        else:
            st.info(f"{caption} diagram not generated yet ({path.name}).")
