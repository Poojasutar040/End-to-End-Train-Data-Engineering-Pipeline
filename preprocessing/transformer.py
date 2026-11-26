"""Feature engineering and route-level aggregation transformations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from utils.config import PATHS
from utils.logger import get_logger
from utils.validators import REQUIRED_RAW_COLUMNS, validate_required_columns

logger = get_logger(__name__)

MINUTES_IN_DAY = 24 * 60


@dataclass(frozen=True)
class TransformationResult:
    """Outputs produced by the schedule transformation step."""

    features_df: pd.DataFrame
    train_summary_df: pd.DataFrame
    train_stops_df: pd.DataFrame
    train_distance_df: pd.DataFrame
    station_summary_df: pd.DataFrame


def _time_to_minutes_since_midnight(series: pd.Series) -> pd.Series:
    """Convert HH:MM:SS string series to minutes since 00:00:00."""
    parsed = pd.to_datetime(series, format="%H:%M:%S", errors="coerce")
    return parsed.dt.hour * 60 + parsed.dt.minute + parsed.dt.second / 60.0


def transform_schedule_data(
    cleaned_df: pd.DataFrame,
    save_outputs: bool = True,
    features_path: Path | None = None,
) -> TransformationResult:
    """Compute leg durations, segment distances, route summaries, and station metrics."""
    validate_required_columns(cleaned_df, REQUIRED_RAW_COLUMNS, dataset_name="Cleaned schedule")

    # Bug fix: sort by Train_No and SN (stop sequence), NOT Route_Number (constant 1)
    df = cleaned_df.sort_values(by=["Train_No", "SN"]).reset_index(drop=True)

    dep_min = _time_to_minutes_since_midnight(df["Departure_Time"])
    arr_min = _time_to_minutes_since_midnight(df["Arrival_time"])

    df["Departure_Hour"] = (dep_min // 60).astype(int)
    df["Arrival_Hour"] = (arr_min // 60).astype(int)

    # Next stop columns within each train
    grouped = df.groupby("Train_No", sort=False)
    df["Next_Station_Code"] = grouped["Station_Code"].shift(-1)
    df["Next_Station_Name"] = grouped["Station_Name"].shift(-1)
    df["Next_Distance"] = grouped["Distance"].shift(-1)
    next_arr_min = arr_min.groupby(df["Train_No"], sort=False).shift(-1)

    # Leg (segment) distance and duration from current departure to next arrival
    df["Segment_Distance"] = df["Next_Distance"] - df["Distance"]
    df.loc[df["Segment_Distance"] < 0, "Segment_Distance"] = np.nan

    leg_duration = next_arr_min - dep_min
    leg_duration = leg_duration.where(leg_duration >= 0, leg_duration + MINUTES_IN_DAY)
    df["Journey_Duration_Minutes"] = leg_duration.round(2)

    # Halt duration at each intermediate stop (0 for origin/terminal stops)
    halt_min = dep_min - arr_min
    halt_min = halt_min.where(halt_min >= 0, halt_min + MINUTES_IN_DAY)
    is_origin = grouped["SN"].transform("min") == df["SN"]
    is_terminal = df["Next_Station_Code"].isna()
    halt_min = halt_min.where(~(is_origin | is_terminal), 0.0)
    # Guard against 00:00:00 placeholder creating artificial multi-hour halt
    halt_min = halt_min.where(halt_min <= 180, 0.0)
    df["Halt_Duration_Minutes"] = halt_min.round(2)

    # Train-level context attached to each stop for ML and search
    df["Total_Train_Stops"] = grouped["SN"].transform("count")
    df["Total_Train_Distance"] = grouped["Distance"].transform("max")
    df["Stop_Order_Index"] = grouped.cumcount() + 1
    df["Stop_Progress_Ratio"] = (df["Stop_Order_Index"] / df["Total_Train_Stops"]).round(4)

    # Segment speed in km/h (used for analytics, avoided as ML leakage feature)
    valid_speed = (df["Journey_Duration_Minutes"] > 0) & (df["Segment_Distance"] >= 0)
    df["Segment_Speed_Kmph"] = np.where(
        valid_speed,
        (df["Segment_Distance"] / (df["Journey_Duration_Minutes"] / 60.0)).round(2),
        np.nan,
    )

    df = df.drop(columns=["Next_Distance"])

    # Aggregated table 1: Number of stops per train
    train_stops_df = (
        df.groupby("Train_No", as_index=False)
        .size()
        .rename(columns={"size": "Number_of_Stops"})
    )

    # Aggregated table 2: Total distance per train
    train_distance_df = (
        df.groupby("Train_No", as_index=False)["Distance"]
        .max()
        .rename(columns={"Distance": "Total_Distance"})
    )

    # Train-level route summary (origin -> destination, total duration across all legs + halts)
    first_stops = df.groupby("Train_No", as_index=False).first()
    last_stops = df.groupby("Train_No", as_index=False).last()
    duration_sums = df.groupby("Train_No", as_index=False).agg(
        Total_Leg_Minutes=("Journey_Duration_Minutes", "sum"),
        Total_Halt_Minutes=("Halt_Duration_Minutes", "sum"),
        Max_1A_Fare=("1A", "max"),
        Max_2A_Fare=("2A", "max"),
        Max_3A_Fare=("3A", "max"),
        Max_SL_Fare=("SL", "max"),
    )

    train_summary_df = pd.DataFrame(
        {
            "Train_No": first_stops["Train_No"],
            "Origin_Code": first_stops["Station_Code"],
            "Origin_Name": first_stops["Station_Name"],
            "Origin_Departure": first_stops["Departure_Time"],
            "Destination_Code": last_stops["Station_Code"],
            "Destination_Name": last_stops["Station_Name"],
            "Destination_Arrival": last_stops["Arrival_time"],
            "Number_of_Stops": train_stops_df["Number_of_Stops"],
            "Total_Distance": train_distance_df["Total_Distance"],
        }
    ).merge(duration_sums, on="Train_No", how="left")

    train_summary_df["Total_Journey_Duration_Minutes"] = (
        train_summary_df["Total_Leg_Minutes"] + train_summary_df["Total_Halt_Minutes"]
    ).round(2)
    train_summary_df["Avg_Speed_Kmph"] = np.where(
        train_summary_df["Total_Journey_Duration_Minutes"] > 0,
        (
            train_summary_df["Total_Distance"]
            / (train_summary_df["Total_Journey_Duration_Minutes"] / 60.0)
        ).round(2),
        0.0,
    )

    # Station-level summary
    origin_counts = first_stops.groupby("Station_Code").size().rename("Origin_Train_Count")
    dest_counts = last_stops.groupby("Station_Code").size().rename("Destination_Train_Count")
    station_summary_df = (
        df.groupby(["Station_Code", "Station_Name"], as_index=False)
        .agg(
            Total_Train_Visits=("Train_No", "nunique"),
            Total_Schedule_Rows=("Train_No", "count"),
            Avg_Halt_Minutes=("Halt_Duration_Minutes", "mean"),
        )
        .merge(origin_counts, on="Station_Code", how="left")
        .merge(dest_counts, on="Station_Code", how="left")
        .fillna({"Origin_Train_Count": 0, "Destination_Train_Count": 0})
    )
    station_summary_df["Origin_Train_Count"] = station_summary_df["Origin_Train_Count"].astype(int)
    station_summary_df["Destination_Train_Count"] = station_summary_df[
        "Destination_Train_Count"
    ].astype(int)
    station_summary_df["Avg_Halt_Minutes"] = station_summary_df["Avg_Halt_Minutes"].round(2)

    if save_outputs:
        PATHS.ensure_directories()
        target_features = Path(features_path) if features_path else PATHS.processed_features_csv
        df.to_csv(target_features, index=False)
        train_summary_df.to_csv(PATHS.train_summary_csv, index=False)
        train_stops_df.to_csv(PATHS.train_stops_csv, index=False)
        train_distance_df.to_csv(PATHS.train_distance_csv, index=False)
        station_summary_df.to_csv(PATHS.station_summary_csv, index=False)
        logger.info("Saved processed features (%d rows) and summary tables.", len(df))

    return TransformationResult(
        features_df=df,
        train_summary_df=train_summary_df,
        train_stops_df=train_stops_df,
        train_distance_df=train_distance_df,
        station_summary_df=station_summary_df,
    )
