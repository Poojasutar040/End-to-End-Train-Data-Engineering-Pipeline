"""KPI calculations for the railway analytics dashboard."""

from __future__ import annotations

from typing import Any

import pandas as pd


def compute_dashboard_kpis(
    features_df: pd.DataFrame,
    train_summary_df: pd.DataFrame,
) -> dict[str, Any]:
    """Compute top-level KPI metrics from processed schedule and summary DataFrames."""
    total_trains = int(train_summary_df["Train_No"].nunique())
    total_stations = int(features_df["Station_Code"].nunique())
    total_route_segments = int(features_df["Journey_Duration_Minutes"].notna().sum())
    total_schedule_rows = int(len(features_df))

    avg_total_duration_min = float(train_summary_df["Total_Journey_Duration_Minutes"].mean())
    avg_leg_duration_min = float(features_df["Journey_Duration_Minutes"].dropna().mean())
    avg_distance_km = float(train_summary_df["Total_Distance"].mean())
    max_distance_km = int(train_summary_df["Total_Distance"].max())
    avg_stops_per_train = float(train_summary_df["Number_of_Stops"].mean())

    return {
        "total_trains": total_trains,
        "total_stations": total_stations,
        "total_routes": total_trains,
        "total_route_segments": total_route_segments,
        "total_schedule_rows": total_schedule_rows,
        "avg_journey_duration_min": round(avg_total_duration_min, 2),
        "avg_journey_duration_hours": round(avg_total_duration_min / 60.0, 2),
        "avg_leg_duration_min": round(avg_leg_duration_min, 2),
        "avg_distance_km": round(avg_distance_km, 2),
        "max_distance_km": max_distance_km,
        "avg_stops_per_train": round(avg_stops_per_train, 2),
    }
