"""Centralized project path and environment configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class ProjectPaths:
    """Standardized directory and file paths resolved from the project root."""

    root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    raw_schedule_csv: Path = PROJECT_ROOT / "data" / "raw" / "train_schedule.csv"
    cleaned_schedule_csv: Path = PROJECT_ROOT / "data" / "cleaned" / "validated_train_schedule.csv"
    processed_features_csv: Path = PROJECT_ROOT / "data" / "processed" / "train_features.csv"
    train_summary_csv: Path = PROJECT_ROOT / "data" / "processed" / "train_routes_summary.csv"
    train_stops_csv: Path = PROJECT_ROOT / "data" / "aggregated" / "train_stops.csv"
    train_distance_csv: Path = PROJECT_ROOT / "data" / "aggregated" / "train_distance.csv"
    station_summary_csv: Path = PROJECT_ROOT / "data" / "aggregated" / "station_summary.csv"
    models_dir: Path = PROJECT_ROOT / "models"
    best_model_path: Path = PROJECT_ROOT / "models" / "train_journey_duration_model.pkl"
    model_metrics_path: Path = PROJECT_ROOT / "models" / "model_metrics.json"
    logs_dir: Path = PROJECT_ROOT / "logs"
    reports_output_dir: Path = PROJECT_ROOT / "reports" / "outputs"
    diagrams_dir: Path = PROJECT_ROOT / "diagrams"
    schema_sql_path: Path = PROJECT_ROOT / "database" / "schema.sql"

    def ensure_directories(self) -> None:
        """Create required output directories if they do not exist."""
        for directory in (
            self.raw_schedule_csv.parent,
            self.cleaned_schedule_csv.parent,
            self.processed_features_csv.parent,
            self.train_stops_csv.parent,
            self.models_dir,
            self.logs_dir,
            self.reports_output_dir,
            self.diagrams_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class MySQLConfig:
    """MySQL connection settings loaded from environment variables."""

    host: str
    port: int
    user: str
    password: str
    database: str

    @classmethod
    def from_env(cls) -> "MySQLConfig":
        """Build MySQLConfig from environment variables without hardcoded passwords."""
        port_raw = os.getenv("MYSQL_PORT", "3306").strip()
        try:
            port = int(port_raw)
        except ValueError as exc:
            raise ValueError(f"Invalid MYSQL_PORT value: {port_raw!r}") from exc

        return cls(
            host=os.getenv("MYSQL_HOST", "localhost").strip(),
            port=port,
            user=os.getenv("MYSQL_USER", "root").strip(),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "smart_railway_db").strip(),
        )

    def is_password_configured(self) -> bool:
        """Return True when a non-empty, non-placeholder MySQL password is set."""
        return bool(self.password) and self.password != "your_mysql_password_here"


PATHS = ProjectPaths()
