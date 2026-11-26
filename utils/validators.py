"""Input and DataFrame validation utilities."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

REQUIRED_RAW_COLUMNS = (
    "SN",
    "Train_No",
    "Station_Code",
    "1A",
    "2A",
    "3A",
    "SL",
    "Station_Name",
    "Route_Number",
    "Arrival_time",
    "Departure_Time",
    "Distance",
)


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: Iterable[str] = REQUIRED_RAW_COLUMNS,
    dataset_name: str = "dataset",
) -> None:
    """Raise ValueError if any expected columns are missing from a DataFrame."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"{dataset_name} is missing required columns: {missing}")


def validate_positive_int(value: int | str, field_name: str, min_val: int = 1) -> int:
    """Parse and validate an integer above min_val."""
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid integer.") from exc
    if parsed < min_val:
        raise ValueError(f"{field_name} must be >= {min_val}.")
    return parsed


def validate_non_negative_float(value: float | int | str, field_name: str) -> float:
    """Parse and validate a non-negative floating-point number."""
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid number.") from exc
    if parsed < 0:
        raise ValueError(f"{field_name} cannot be negative.")
    return parsed


def validate_station_code(code: str) -> str:
    """Normalize and validate a railway station code."""
    cleaned = (code or "").strip().upper()
    if not cleaned or len(cleaned) > 10 or not cleaned.replace("-", "").isalnum():
        raise ValueError(
            "Station code must be 1 to 10 alphanumeric characters."
        )
    return cleaned
