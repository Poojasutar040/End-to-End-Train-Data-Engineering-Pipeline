"""CSV ingestion and schema inspection utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from utils.config import PATHS
from utils.logger import get_logger
from utils.validators import REQUIRED_RAW_COLUMNS, validate_required_columns

logger = get_logger(__name__)


@dataclass(frozen=True)
class IngestionResult:
    """Container holding the ingested raw DataFrame and summary metadata."""

    dataframe: pd.DataFrame
    metadata: dict[str, Any]


def load_raw_schedule(csv_path: Path | None = None) -> IngestionResult:
    """Load the raw train schedule CSV and validate its schema.

    The raw source file is read-only and never modified in place.
    """
    source = Path(csv_path) if csv_path else PATHS.raw_schedule_csv
    if not source.exists():
        raise FileNotFoundError(f"Raw dataset not found at: {source}")

    logger.info("Reading raw train schedule from %s", source)
    df = pd.read_csv(source, low_memory=False)
    validate_required_columns(df, REQUIRED_RAW_COLUMNS, dataset_name="Raw train schedule")

    metadata: dict[str, Any] = {
        "source_path": str(source),
        "total_records": int(df.shape[0]),
        "total_columns": int(df.shape[1]),
        "columns": df.columns.tolist(),
        "unique_trains": int(df["Train_No"].nunique()),
        "unique_station_codes": int(df["Station_Code"].astype(str).str.strip().nunique()),
        "missing_values": {col: int(cnt) for col, cnt in df.isnull().sum().items()},
        "duplicate_rows": int(df.duplicated().sum()),
    }
    logger.info(
        "Ingested %d records across %d unique trains and %d station codes.",
        metadata["total_records"],
        metadata["unique_trains"],
        metadata["unique_station_codes"],
    )
    return IngestionResult(dataframe=df, metadata=metadata)
