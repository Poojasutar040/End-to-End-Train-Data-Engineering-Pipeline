"""Generate downloadable CSV and Markdown summary reports."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from utils.config import PATHS


def generate_markdown_summary_report(
    kpis: dict[str, Any],
    longest_routes: pd.DataFrame,
    busiest_stations: pd.DataFrame,
    ml_metrics: dict[str, Any] | None = None,
    output_path: Path | None = None,
) -> Path:
    """Write a structured Markdown analytical report and return its file path."""
    PATHS.ensure_directories()
    target = Path(output_path) if output_path else (PATHS.reports_output_dir / "railway_analytics_report.md")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Smart Railway Analytics & Train Journey Prediction Report",
        f"**Generated:** {generated_at}",
        "",
        "## 1. Executive KPIs",
        f"- **Total Trains:** {kpis.get('total_trains', 0):,}",
        f"- **Total Stations:** {kpis.get('total_stations', 0):,}",
        f"- **Total Route Segments:** {kpis.get('total_route_segments', 0):,}",
        f"- **Average Total Journey Duration:** {kpis.get('avg_journey_duration_min', 0)} min ({kpis.get('avg_journey_duration_hours', 0)} hrs)",
        f"- **Average Leg Duration:** {kpis.get('avg_leg_duration_min', 0)} min",
        f"- **Average Route Distance:** {kpis.get('avg_distance_km', 0)} km",
        f"- **Maximum Route Distance:** {kpis.get('max_distance_km', 0):,} km",
        "",
        "## 2. Top 10 Longest Train Routes",
        "| Train No | Origin | Destination | Stops | Distance (km) | Duration (min) |",
        "|---:|---|---|---:|---:|---:|",
    ]

    for row in longest_routes.head(10).itertuples(index=False):
        lines.append(
            f"| {row.Train_No} | {row.Origin_Name} ({row.Origin_Code}) | "
            f"{row.Destination_Name} ({row.Destination_Code}) | {row.Number_of_Stops} | "
            f"{row.Total_Distance:,} | {row.Total_Journey_Duration_Minutes:.1f} |"
        )

    lines.extend(
        [
            "",
            "## 3. Top 10 Busiest Railway Stations",
            "| Station Code | Station Name | Trains Visiting | Origin Count | Destination Count | Avg Halt (min) |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in busiest_stations.head(10).itertuples(index=False):
        lines.append(
            f"| {row.Station_Code} | {row.Station_Name} | {row.Total_Train_Visits:,} | "
            f"{row.Origin_Train_Count:,} | {row.Destination_Train_Count:,} | {row.Avg_Halt_Minutes:.1f} |"
        )

    if ml_metrics and ml_metrics.get("models"):
        lines.extend(
            [
                "",
                "## 4. Machine Learning Model Comparison",
                f"**Best Model Selected:** {ml_metrics.get('best_model')}",
                "",
                "| Model | MAE (min) | RMSE (min) | R2 Score |",
                "|---|---:|---:|---:|",
            ]
        )
        for m in ml_metrics["models"]:
            lines.append(
                f"| {m['model_name']} | {m['mae']:.4f} | {m['rmse']:.4f} | {m['r2']:.4f} |"
            )

    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def export_route_summary_csv(
    train_summary_df: pd.DataFrame,
    min_distance: int = 0,
    min_stops: int = 1,
    output_path: Path | None = None,
) -> Path:
    """Export filtered train route summary data to CSV."""
    PATHS.ensure_directories()
    filtered = train_summary_df[
        (train_summary_df["Total_Distance"] >= min_distance)
        & (train_summary_df["Number_of_Stops"] >= min_stops)
    ].copy()
    target = Path(output_path) if output_path else (PATHS.reports_output_dir / "filtered_train_routes.csv")
    filtered.to_csv(target, index=False)
    return target
