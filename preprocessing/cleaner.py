"""Data cleaning and standardization for raw train schedule records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from utils.config import PATHS
from utils.logger import get_logger
from utils.validators import REQUIRED_RAW_COLUMNS, validate_required_columns

logger = get_logger(__name__)

NUMERIC_INT_COLUMNS = ("SN", "Train_No", "1A", "2A", "3A", "SL", "Route_Number", "Distance")


@dataclass(frozen=True)
class CleaningSummary:
    """Metrics describing data cleaning operations performed."""

    initial_rows: int
    duplicates_removed: int
    invalid_rows_removed: int
    station_names_standardized: int
    final_rows: int
    output_path: str


def _parse_time_to_hms(series: pd.Series) -> pd.Series:
    """Parse time strings into standardized HH:MM:SS format."""
    cleaned = series.astype(str).str.strip()
    parsed = pd.to_datetime(cleaned, format="%H:%M:%S", errors="coerce")
    missing_mask = parsed.isna()
    if missing_mask.any():
        parsed_hm = pd.to_datetime(cleaned[missing_mask], format="%H:%M", errors="coerce")
        parsed = parsed.fillna(parsed_hm)
    return parsed.dt.strftime("%H:%M:%S")


def _standardize_station_names(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Ensure each Station_Code maps to a single canonical Station_Name."""
    code_name_counts = df.groupby("Station_Code")["Station_Name"].nunique()
    inconsistent_codes = code_name_counts[code_name_counts > 1].index

    if len(inconsistent_codes) == 0:
        return df, 0

    canonical_map = (
        df[df["Station_Code"].isin(inconsistent_codes)]
        .groupby("Station_Code")["Station_Name"]
        .agg(lambda s: s.mode().iloc[0])
        .to_dict()
    )
    before = df["Station_Name"].copy()
    df["Station_Name"] = df["Station_Code"].map(canonical_map).fillna(df["Station_Name"])
    changed_rows = int((before != df["Station_Name"]).sum())
    logger.info(
        "Standardized %d station codes (%d rows) to canonical station names.",
        len(inconsistent_codes),
        changed_rows,
    )
    return df, changed_rows


def clean_schedule_data(
    raw_df: pd.DataFrame,
    output_path: Path | None = None,
) -> tuple[pd.DataFrame, CleaningSummary]:
    """Clean, deduplicate, validate, and standardize raw schedule records."""
    validate_required_columns(raw_df, REQUIRED_RAW_COLUMNS, dataset_name="Raw schedule")
    df = raw_df.copy()
    initial_rows = len(df)

    # Normalize string columns
    for col in ("Station_Code", "Station_Name"):
        df[col] = df[col].astype(str).str.strip().str.upper()

    # Coerce numeric fields safely
    for col in NUMERIC_INT_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Standardize times cleanly as HH:MM:SS
    df["Arrival_time"] = _parse_time_to_hms(df["Arrival_time"])
    df["Departure_Time"] = _parse_time_to_hms(df["Departure_Time"])

    # Drop rows missing critical identifiers or invalid times
    required_non_null = [
        "SN",
        "Train_No",
        "Station_Code",
        "Station_Name",
        "Arrival_time",
        "Departure_Time",
        "Distance",
    ]
    before_valid = len(df)
    df = df.dropna(subset=required_non_null)
    df = df[df["Distance"] >= 0]
    invalid_rows_removed = before_valid - len(df)

    # Convert integer columns back to int64 after dropping NaNs
    for col in NUMERIC_INT_COLUMNS:
        df[col] = df[col].astype("int64")

    # Remove exact duplicates and duplicate (Train_No, SN) keys
    before_dedup = len(df)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=["Train_No", "SN"], keep="first")
    duplicates_removed = before_dedup - len(df)

    # Sort deterministically by Train_No and stop sequence SN
    df = df.sort_values(by=["Train_No", "SN"]).reset_index(drop=True)

    # Resolve Station_Code -> Station_Name naming mismatches
    df, station_names_standardized = _standardize_station_names(df)

    target_path = Path(output_path) if output_path else PATHS.cleaned_schedule_csv
    target_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target_path, index=False)

    summary = CleaningSummary(
        initial_rows=initial_rows,
        duplicates_removed=duplicates_removed,
        invalid_rows_removed=invalid_rows_removed,
        station_names_standardized=station_names_standardized,
        final_rows=len(df),
        output_path=str(target_path),
    )
    logger.info(
        "Cleaning finished: %d -> %d rows (duplicates=%d, invalid=%d).",
        initial_rows,
        len(df),
        duplicates_removed,
        invalid_rows_removed,
    )
    return df, summary
