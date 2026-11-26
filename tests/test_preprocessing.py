"""Unit tests for data cleaning and schedule transformation."""

from __future__ import annotations

import pandas as pd

from preprocessing.cleaner import clean_schedule_data
from preprocessing.transformer import transform_schedule_data


def _sample_raw_df() -> pd.DataFrame:
    # Intentionally out-of-order SN + duplicate row + station name mismatch + overnight leg
    return pd.DataFrame(
        [
            {
                "SN": 2,
                "Train_No": 107,
                "Station_Code": "THVM",
                "1A": 260,
                "2A": 228,
                "3A": 196,
                "SL": 164,
                "Station_Name": "THIVIM",
                "Route_Number": 1,
                "Arrival_time": "00:30:00",
                "Departure_Time": "00:35:00",
                "Distance": 32,
            },
            {
                "SN": 1,
                "Train_No": 107,
                "Station_Code": "SWV",
                "1A": 100,
                "2A": 100,
                "3A": 100,
                "SL": 100,
                "Station_Name": "SAWANTWADI R",
                "Route_Number": 1,
                "Arrival_time": "00:00:00",
                "Departure_Time": "23:50:00",
                "Distance": 0,
            },
            {
                "SN": 1,
                "Train_No": 107,
                "Station_Code": "SWV",
                "1A": 100,
                "2A": 100,
                "3A": 100,
                "SL": 100,
                "Station_Name": "SAWANTWADI R",
                "Route_Number": 1,
                "Arrival_time": "00:00:00",
                "Departure_Time": "23:50:00",
                "Distance": 0,
            },
        ]
    )


def test_clean_and_transform_sorts_by_sn_and_handles_midnight(tmp_path) -> None:
    cleaned, summary = clean_schedule_data(_sample_raw_df(), output_path=tmp_path / "clean.csv")
    assert summary.duplicates_removed == 1
    assert cleaned["SN"].tolist() == [1, 2]

    transformed = transform_schedule_data(cleaned, save_outputs=False)
    feat = transformed.features_df
    assert feat.iloc[0]["Station_Code"] == "SWV"
    assert feat.iloc[0]["Segment_Distance"] == 32
    # 23:50:00 -> 00:30:00 next day = 40 minutes
    assert feat.iloc[0]["Journey_Duration_Minutes"] == 40.0
    assert pd.isna(feat.iloc[1]["Journey_Duration_Minutes"])
