"""Cached data, model, and database status loaders for the Streamlit UI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analytics.kpis import compute_dashboard_kpis
from database.connection import test_connection
from models.predictor import JourneyDurationPredictor
from utils.config import PATHS


@st.cache_data(show_spinner="Loading processed railway datasets...")
def load_dashboard_datasets() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load processed features, train route summaries, and station summaries."""
    if not PATHS.processed_features_csv.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at {PATHS.processed_features_csv}. "
            "Please run 'python main.py --skip-db' first."
        )
    features_df = pd.read_csv(PATHS.processed_features_csv, low_memory=False)
    train_summary_df = pd.read_csv(PATHS.train_summary_csv, low_memory=False)
    station_summary_df = pd.read_csv(PATHS.station_summary_csv, low_memory=False)
    return features_df, train_summary_df, station_summary_df


@st.cache_data
def get_cached_kpis() -> dict:
    """Compute and cache top-level dashboard KPIs."""
    features_df, train_summary_df, _ = load_dashboard_datasets()
    return compute_dashboard_kpis(features_df, train_summary_df)


@st.cache_resource
def get_cached_predictor() -> JourneyDurationPredictor:
    """Load and cache the persisted ML predictor."""
    return JourneyDurationPredictor()


def get_mysql_status() -> tuple[bool, str]:
    """Check current MySQL connectivity status without crashing the UI."""
    return test_connection()
