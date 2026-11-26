"""Unit tests for ML training, evaluation metrics, and prediction validation."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from models.predictor import JourneyDurationPredictor
from models.trainer import train_and_evaluate_models


def _synthetic_features_df(n_rows: int = 120) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    seg_dist = rng.integers(10, 200, size=n_rows)
    total_dist = seg_dist + rng.integers(50, 800, size=n_rows)
    total_stops = rng.integers(5, 30, size=n_rows)
    stop_idx = rng.integers(1, 5, size=n_rows)
    dep_hour = rng.integers(0, 24, size=n_rows)
    halt_min = rng.integers(1, 15, size=n_rows)
    duration = seg_dist * 1.1 + halt_min * 0.5 + rng.normal(0, 2, size=n_rows)
    return pd.DataFrame(
        {
            "Segment_Distance": seg_dist.astype(float),
            "Total_Train_Distance": total_dist.astype(float),
            "Total_Train_Stops": total_stops,
            "Stop_Order_Index": stop_idx,
            "Departure_Hour": dep_hour,
            "Halt_Duration_Minutes": halt_min.astype(float),
            "Journey_Duration_Minutes": np.clip(duration, 5, 400),
        }
    )


def test_train_evaluate_and_predict(tmp_path) -> None:
    df = _synthetic_features_df()
    model_path = tmp_path / "model.pkl"
    metrics_path = tmp_path / "metrics.json"

    report = train_and_evaluate_models(df, model_output_path=model_path, metrics_output_path=metrics_path)
    assert model_path.exists()
    assert metrics_path.exists()
    assert len(report["models"]) == 3
    assert report["best_model"] in {"Linear Regression", "Decision Tree", "Random Forest"}

    predictor = JourneyDurationPredictor(model_path=model_path)
    validated = predictor.validate_inputs(
        segment_distance=80,
        total_train_distance=500,
        total_train_stops=10,
        stop_order_index=3,
        departure_hour=12,
        halt_duration_minutes=5,
    )
    pred = predictor.predict_leg_duration(validated)
    assert pred > 0

    with pytest.raises(ValueError, match="Total Train Distance"):
        predictor.validate_inputs(200, 100, 10, 2, 10, 2)
