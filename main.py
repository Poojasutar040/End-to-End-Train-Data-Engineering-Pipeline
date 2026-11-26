"""CLI orchestrator for the Smart Railway Analytics ETL, MySQL, and ML pipeline."""

from __future__ import annotations

import argparse

from analytics.kpis import compute_dashboard_kpis
from database.connection import DatabaseConnectionError, test_connection
from database.loader import load_all_to_mysql
from ingestion.loader import load_raw_schedule
from models.trainer import train_and_evaluate_models
from preprocessing.cleaner import clean_schedule_data
from preprocessing.transformer import transform_schedule_data
from utils.config import PATHS, MySQLConfig
from utils.logger import get_logger

logger = get_logger(__name__)


def run_pipeline(load_db: bool = True) -> dict[str, object]:
    """Execute ingestion, cleaning, transformation, ML training, and optional MySQL load."""
    PATHS.ensure_directories()

    logger.info("=== STEP 1: DATA INGESTION ===")
    ingestion_res = load_raw_schedule()

    logger.info("=== STEP 2: DATA CLEANING & VALIDATION ===")
    cleaned_df, cleaning_summary = clean_schedule_data(ingestion_res.dataframe)

    logger.info("=== STEP 3: TRANSFORMATION & FEATURE ENGINEERING ===")
    transformed = transform_schedule_data(cleaned_df, save_outputs=True)

    logger.info("=== STEP 4: KPI SUMMARY ===")
    kpis = compute_dashboard_kpis(transformed.features_df, transformed.train_summary_df)
    logger.info("KPIs: %s", kpis)

    logger.info("=== STEP 5: MACHINE LEARNING TRAINING & EVALUATION ===")
    ml_report = train_and_evaluate_models(transformed.features_df)
    logger.info("Best ML model: %s", ml_report["best_model"])

    db_status = "Skipped"
    db_counts: dict[str, int] = {}
    if load_db:
        cfg = MySQLConfig.from_env()
        if not cfg.is_password_configured():
            db_status = "Not configured (.env MYSQL_PASSWORD missing)"
            logger.warning(
                "MySQL load skipped: copy .env.example to .env and set MYSQL_PASSWORD to enable MySQL."
            )
        else:
            ok, msg = test_connection(cfg)
            if ok:
                try:
                    db_counts = load_all_to_mysql(
                        transformed.features_df,
                        transformed.train_summary_df,
                        cfg,
                    )
                    db_status = f"Loaded successfully: {db_counts}"
                except DatabaseConnectionError as exc:
                    db_status = f"Error: {exc}"
                    logger.error(db_status)
            else:
                db_status = f"Unavailable: {msg}"
                logger.warning("MySQL load skipped: %s", msg)

    return {
        "ingestion": ingestion_res.metadata,
        "cleaning": cleaning_summary,
        "kpis": kpis,
        "ml_report": ml_report,
        "db_status": db_status,
        "db_counts": db_counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Smart Railway Analytics ETL, MySQL, and ML pipeline."
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip MySQL database loading even if .env is configured.",
    )
    args = parser.parse_args()

    summary = run_pipeline(load_db=not args.skip_db)
    print("\n================ PIPELINE SUMMARY ================")
    print("Total Trains       :", summary["kpis"]["total_trains"])
    print("Total Stations     :", summary["kpis"]["total_stations"])
    print("Total Route Legs   :", summary["kpis"]["total_route_segments"])
    print("Avg Total Duration :", summary["kpis"]["avg_journey_duration_min"], "min")
    print("Best ML Model      :", summary["ml_report"]["best_model"])
    for model_row in summary["ml_report"]["models"]:
        print(
            f"  - {model_row['model_name']:18s} | MAE={model_row['mae']:.4f} | "
            f"RMSE={model_row['rmse']:.4f} | R2={model_row['r2']:.4f}"
        )
    print("MySQL Status       :", summary["db_status"])
    print("==================================================\n")


if __name__ == "__main__":
    main()
