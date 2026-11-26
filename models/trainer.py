"""Train, evaluate, compare, and persist regression models for journey duration prediction."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

from utils.config import PATHS
from utils.logger import get_logger
from utils.validators import validate_required_columns

logger = get_logger(__name__)

FEATURE_COLUMNS = [
    "Segment_Distance",
    "Total_Train_Distance",
    "Total_Train_Stops",
    "Stop_Order_Index",
    "Departure_Hour",
    "Halt_Duration_Minutes",
]
TARGET_COLUMN = "Journey_Duration_Minutes"


@dataclass(frozen=True)
class ModelMetrics:
    """Evaluation metrics for a trained regression model."""

    model_name: str
    mae: float
    rmse: float
    r2: float


def prepare_ml_dataset(features_df: pd.DataFrame) -> pd.DataFrame:
    """Filter and clean feature + target columns for supervised regression."""
    validate_required_columns(
        features_df,
        [*FEATURE_COLUMNS, TARGET_COLUMN],
        dataset_name="Processed train features",
    )
    ml_df = features_df[[*FEATURE_COLUMNS, TARGET_COLUMN]].dropna().copy()
    ml_df = ml_df[
        (ml_df["Segment_Distance"] > 0)
        & (ml_df[TARGET_COLUMN] > 0)
        & (ml_df[TARGET_COLUMN] <= 1440)
    ]
    return ml_df.reset_index(drop=True)


def _extract_feature_importance(model: Any, feature_names: list[str]) -> dict[str, float]:
    """Extract normalized feature importance or absolute standardized coefficients."""
    estimator = model.named_steps["regressor"] if isinstance(model, Pipeline) else model
    if hasattr(estimator, "feature_importances_"):
        importances = np.asarray(estimator.feature_importances_, dtype=float)
    elif hasattr(estimator, "coef_"):
        importances = np.abs(np.asarray(estimator.coef_, dtype=float))
        total = importances.sum()
        if total > 0:
            importances = importances / total
    else:
        return {}
    return {
        name: round(float(val), 4)
        for name, val in sorted(zip(feature_names, importances), key=lambda item: item[1], reverse=True)
    }


def train_and_evaluate_models(
    features_df: pd.DataFrame,
    model_output_path: Path | None = None,
    metrics_output_path: Path | None = None,
    test_size: float = 0.20,
    random_state: int = 42,
) -> dict[str, Any]:
    """Train Linear Regression, Decision Tree, and Random Forest; save the best model."""
    ml_df = prepare_ml_dataset(features_df)
    if len(ml_df) < 50:
        raise ValueError(f"Insufficient training records ({len(ml_df)}). Need at least 50.")

    X = ml_df[FEATURE_COLUMNS]
    y = ml_df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    candidates: dict[str, Any] = {
        "Linear Regression": Pipeline(
            [("scaler", StandardScaler()), ("regressor", LinearRegression())]
        ),
        "Decision Tree": DecisionTreeRegressor(
            max_depth=12,
            min_samples_leaf=10,
            random_state=random_state,
        ),
        "Random Forest": RandomForestRegressor(
            n_estimators=80,
            max_depth=14,
            min_samples_leaf=5,
            random_state=random_state,
            n_jobs=-1,
        ),
    }

    results: list[ModelMetrics] = []
    trained_models: dict[str, Any] = {}

    for name, estimator in candidates.items():
        logger.info("Training %s on %d samples...", name, len(X_train))
        estimator.fit(X_train, y_train)
        preds = estimator.predict(X_test)
        mae = float(mean_absolute_error(y_test, preds))
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        r2 = float(r2_score(y_test, preds))

        results.append(
            ModelMetrics(
                model_name=name,
                mae=round(mae, 4),
                rmse=round(rmse, 4),
                r2=round(r2, 4),
            )
        )
        trained_models[name] = estimator
        logger.info("%s -> MAE=%.4f, RMSE=%.4f, R2=%.4f", name, mae, rmse, r2)

    # Best model selected by lowest RMSE (tie-broken by highest R2)
    best_metric = min(results, key=lambda m: (m.rmse, -m.r2))
    best_model_name = best_metric.model_name
    best_model = trained_models[best_model_name]

    feature_importance = _extract_feature_importance(best_model, FEATURE_COLUMNS)

    # Sample actual vs predicted for visualization (up to 500 points)
    best_preds = best_model.predict(X_test)
    sample_n = min(500, len(y_test))
    sample_df = pd.DataFrame(
        {
            "actual": y_test.iloc[:sample_n].round(2).tolist(),
            "predicted": np.round(best_preds[:sample_n], 2).tolist(),
        }
    )

    bundle = {
        "model": best_model,
        "model_name": best_model_name,
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "metrics": asdict(best_metric),
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }

    target_model_path = Path(model_output_path) if model_output_path else PATHS.best_model_path
    target_metrics_path = Path(metrics_output_path) if metrics_output_path else PATHS.model_metrics_path
    target_model_path.parent.mkdir(parents=True, exist_ok=True)
    target_metrics_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(bundle, target_model_path)

    report_payload = {
        "best_model": best_model_name,
        "training_samples": int(len(X_train)),
        "testing_samples": int(len(X_test)),
        "features": FEATURE_COLUMNS,
        "target": TARGET_COLUMN,
        "models": [asdict(m) for m in results],
        "feature_importance": feature_importance,
        "sample_predictions": sample_df.to_dict(orient="list"),
        "trained_at": bundle["trained_at"],
    }
    target_metrics_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

    logger.info("Saved best model (%s) to %s", best_model_name, target_model_path)
    return report_payload
