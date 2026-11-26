"""Unit tests for data ingestion."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from ingestion.loader import load_raw_schedule


def test_load_raw_schedule_valid(tmp_path: Path) -> None:
    csv_file = tmp_path / "sample.csv"
    df = pd.DataFrame(
        [
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
                "Departure_Time": "10:25:00",
                "Distance": 0,
            }
        ]
    )
    df.to_csv(csv_file, index=False)

    res = load_raw_schedule(csv_file)
    assert res.metadata["total_records"] == 1
    assert res.metadata["unique_trains"] == 1
    assert len(res.dataframe) == 1


def test_load_raw_schedule_missing_columns(tmp_path: Path) -> None:
    csv_file = tmp_path / "bad.csv"
    pd.DataFrame([{"Train_No": 107}]).to_csv(csv_file, index=False)

    with pytest.raises(ValueError, match="missing required columns"):
        load_raw_schedule(csv_file)
