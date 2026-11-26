"""Route-level and station-level analytical queries."""

from __future__ import annotations

import pandas as pd


def get_longest_and_shortest_routes(
    train_summary_df: pd.DataFrame,
    top_n: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return top-N longest and shortest routes by Total_Distance (excluding 0-km anomalies)."""
    valid = train_summary_df[train_summary_df["Total_Distance"] > 0].copy()
    longest = valid.nlargest(top_n, "Total_Distance").reset_index(drop=True)
    shortest = valid.nsmallest(top_n, "Total_Distance").reset_index(drop=True)
    return longest, shortest


def get_busiest_stations(
    station_summary_df: pd.DataFrame,
    top_n: int = 15,
) -> pd.DataFrame:
    """Return top-N busiest stations ranked by unique trains visiting."""
    return station_summary_df.nlargest(top_n, "Total_Train_Visits").reset_index(drop=True)


def get_train_route_profile(features_df: pd.DataFrame, train_no: int) -> pd.DataFrame:
    """Return stop-level cumulative distance, segment duration, and fare progression for one train."""
    profile = features_df[features_df["Train_No"] == int(train_no)].sort_values("SN").copy()
    return profile.reset_index(drop=True)
