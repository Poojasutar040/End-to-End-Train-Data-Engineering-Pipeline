"""Data ingestion package for loading and verifying raw railway datasets."""

from ingestion.loader import IngestionResult, load_raw_schedule

__all__ = ["IngestionResult", "load_raw_schedule"]
