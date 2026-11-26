"""Unit tests for railway KPIs, search, and route analysis."""

from __future__ import annotations

import pandas as pd
import pytest

from analytics.kpis import compute_dashboard_kpis
from analytics.search import search_between_stations, search_by_station, search_by_train_number
from preprocessing.cleaner import clean_schedule_data
from preprocessing.transformer import transform_schedule_data


def _transformed_fixture():
    raw = pd.DataFrame(
        [
            {"SN": 1, "Train_No": 107, "Station_Code": "SWV", "1A": 100, "2A": 100, "3A": 100, "SL": 100, "Station_Name": "SAWANTWADI R", "Route_Number": 1, "Arrival_time": "00:00:00", "Departure_Time": "10:25:00", "Distance": 0},
            {"SN": 2, "Train_No": 107, "Station_Code": "THVM", "1A": 260, "2A": 228, "3A": 196, "SL": 164, "Station_Name": "THIVIM", "Route_Number": 1, "Arrival_time": "11:06:00", "Departure_Time": "11:08:00", "Distance": 32},
            {"SN": 3, "Train_No": 107, "Station_Code": "MAO", "1A": 490, "2A": 412, "3A": 334, "SL": 256, "Station_Name": "MADGOAN JN.", "Route_Number": 1, "Arrival_time": "12:10:00", "Departure_Time": "00:00:00", "Distance": 78},
        ]
    )
    cleaned, _ = clean_schedule_data(raw)
    return transform_schedule_data(cleaned, save_outputs=False)


def test_kpis_and_search() -> None:
    res = _transformed_fixture()
    kpis = compute_dashboard_kpis(res.features_df, res.train_summary_df)
    assert kpis["total_trains"] == 1
    assert kpis["total_stations"] == 3
    assert kpis["total_route_segments"] == 2

    train_sched = search_by_train_number(res.features_df, 107)
    assert len(train_sched) == 3

    station_hits = search_by_station(res.features_df, "THIVIM")
    assert len(station_hits) == 1

    od_hits = search_between_stations(res.features_df, "SWV", "MAO")
    assert len(od_hits) == 1
    assert od_hits.iloc[0]["Journey_Distance_Km"] == 78
    # 10:25 -> 11:06 (41m) + 2m halt + 11:08 -> 12:10 (62m) = 105m
    assert od_hits.iloc[0]["Scheduled_Duration_Minutes"] == 105.0

    with pytest.raises(ValueError):
        search_between_stations(res.features_df, "SWV", "SWV")
