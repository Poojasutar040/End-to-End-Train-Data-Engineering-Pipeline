"""Train and station search functions supporting number, station, and OD pair queries."""

from __future__ import annotations

import pandas as pd

from utils.validators import validate_positive_int


def search_by_train_number(features_df: pd.DataFrame, train_no: int | str) -> pd.DataFrame:
    """Return the ordered stop-by-stop schedule for a specific train number."""
    tno = validate_positive_int(train_no, "Train Number")
    result = features_df[features_df["Train_No"] == tno].sort_values("SN").copy()
    return result.reset_index(drop=True)


def search_by_station(features_df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Find trains stopping at stations matching code or name (case-insensitive)."""
    cleaned = (query or "").strip().upper()
    if not cleaned:
        raise ValueError("Please enter a station code or station name to search.")

    mask = features_df["Station_Code"].str.upper().str.contains(cleaned, na=False, regex=False) | (
        features_df["Station_Name"].str.upper().str.contains(cleaned, na=False, regex=False)
    )
    cols = [
        "Train_No",
        "SN",
        "Station_Code",
        "Station_Name",
        "Arrival_time",
        "Departure_Time",
        "Distance",
        "Total_Train_Stops",
        "Total_Train_Distance",
    ]
    available_cols = [c for c in cols if c in features_df.columns]
    return features_df.loc[mask, available_cols].sort_values(["Train_No", "SN"]).reset_index(drop=True)


def search_between_stations(
    features_df: pd.DataFrame,
    origin_query: str,
    destination_query: str,
) -> pd.DataFrame:
    """Find trains traveling from origin station to destination station in route order."""
    orig = (origin_query or "").strip().upper()
    dest = (destination_query or "").strip().upper()
    if not orig or not dest:
        raise ValueError("Both origin and destination station queries are required.")
    if orig == dest:
        raise ValueError("Origin and destination stations must be different.")

    orig_mask = (features_df["Station_Code"].str.upper() == orig) | (
        features_df["Station_Name"].str.upper().str.contains(orig, na=False, regex=False)
    )
    dest_mask = (features_df["Station_Code"].str.upper() == dest) | (
        features_df["Station_Name"].str.upper().str.contains(dest, na=False, regex=False)
    )

    orig_stops = features_df.loc[
        orig_mask,
        ["Train_No", "SN", "Station_Code", "Station_Name", "Departure_Time", "Distance", "1A", "2A", "3A", "SL"],
    ].rename(
        columns={
            "SN": "Origin_SN",
            "Station_Code": "Origin_Code",
            "Station_Name": "Origin_Name",
            "Departure_Time": "Origin_Departure",
            "Distance": "Origin_Distance",
            "1A": "Origin_1A",
            "2A": "Origin_2A",
            "3A": "Origin_3A",
            "SL": "Origin_SL",
        }
    )

    dest_stops = features_df.loc[
        dest_mask,
        ["Train_No", "SN", "Station_Code", "Station_Name", "Arrival_time", "Distance", "1A", "2A", "3A", "SL"],
    ].rename(
        columns={
            "SN": "Dest_SN",
            "Station_Code": "Dest_Code",
            "Station_Name": "Dest_Name",
            "Arrival_time": "Dest_Arrival",
            "Distance": "Dest_Distance",
            "1A": "Dest_1A",
            "2A": "Dest_2A",
            "3A": "Dest_3A",
            "SL": "Dest_SL",
        }
    )

    merged = orig_stops.merge(dest_stops, on="Train_No", how="inner")
    valid = merged[merged["Origin_SN"] < merged["Dest_SN"]].copy()
    if valid.empty:
        return pd.DataFrame()

    valid["Journey_Distance_Km"] = valid["Dest_Distance"] - valid["Origin_Distance"]
    valid["Intermediate_Stops"] = valid["Dest_SN"] - valid["Origin_SN"]
    valid["Est_SL_Fare"] = (valid["Dest_SL"] - valid["Origin_SL"]).clip(lower=0)
    valid["Est_3A_Fare"] = (valid["Dest_3A"] - valid["Origin_3A"]).clip(lower=0)

    # Compute exact scheduled duration across the sub-route legs and intermediate halts
    def _subroute_duration(row: pd.Series) -> float:
        sub = features_df[
            (features_df["Train_No"] == row["Train_No"])
            & (features_df["SN"] >= row["Origin_SN"])
            & (features_df["SN"] < row["Dest_SN"])
        ]
        leg_sum = sub["Journey_Duration_Minutes"].fillna(0).sum()
        halt_sum = sub.iloc[1:]["Halt_Duration_Minutes"].fillna(0).sum() if len(sub) > 1 else 0.0
        return round(float(leg_sum + halt_sum), 2)

    valid["Scheduled_Duration_Minutes"] = valid.apply(_subroute_duration, axis=1)

    display_cols = [
        "Train_No",
        "Origin_Code",
        "Origin_Name",
        "Origin_Departure",
        "Dest_Code",
        "Dest_Name",
        "Dest_Arrival",
        "Intermediate_Stops",
        "Journey_Distance_Km",
        "Scheduled_Duration_Minutes",
        "Est_SL_Fare",
        "Est_3A_Fare",
    ]
    return valid[display_cols].sort_values("Journey_Distance_Km", ascending=False).reset_index(drop=True)
