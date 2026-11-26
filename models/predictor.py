"""Model inference service for predicting scheduled train journey durations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from models.trainer import FEATURE_COLUMNS
from utils.config import PATHS
from utils.validators import validate_non_negative_float, validate_positive_int


@dataclass(frozen=True)
class PredictionInput:
    """Validated inputs required for single-leg scheduled duration prediction."""

    segment_distance: float
    total_train_distance: float
    total_train_stops: int
    stop_order_index: int
    departure_hour: int
    halt_duration_minutes: float

    def to_dataframe(self, columns: list[str] | None = None) -> pd.DataFrame:
        row = {
            "Segment_Distance": self.segment_distance,
            "Total_Train_Distance": self.total_train_distance,
            "Total_Train_Stops": self.total_train_stops,
            "Stop_Order_Index": self.stop_order_index,
            "Departure_Hour": self.departure_hour,
            "Halt_Duration_Minutes": self.halt_duration_minutes,
        }
        cols = columns or FEATURE_COLUMNS
        return pd.DataFrame([[row[c] for c in cols]], columns=cols)


class JourneyDurationPredictor:
    """Loads the persisted ML bundle and predicts scheduled leg/route durations."""

    def __init__(self, model_path: Path | None = None) -> None:
        self.model_path = Path(model_path) if model_path else PATHS.best_model_path
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Trained model not found at {self.model_path}. Run main.py to train models first."
            )
        bundle = joblib.load(self.model_path)
        if isinstance(bundle, dict) and "model" in bundle:
            self.model = bundle["model"]
            self.model_name = str(bundle.get("model_name", type(self.model).__name__))
            self.feature_columns = list(bundle.get("feature_columns", FEATURE_COLUMNS))
            self.metrics = bundle.get("metrics", {})
        else:
            self.model = bundle
            self.model_name = type(bundle).__name__
            self.feature_columns = FEATURE_COLUMNS
            self.metrics = {}

    def validate_inputs(
        self,
        segment_distance: float,
        total_train_distance: float,
        total_train_stops: int,
        stop_order_index: int,
        departure_hour: int,
        halt_duration_minutes: float,
    ) -> PredictionInput:
        """Validate user inputs before running inference."""
        seg_dist = validate_non_negative_float(segment_distance, "Segment Distance (km)")
        if seg_dist <= 0:
            raise ValueError("Segment Distance (km) must be greater than 0.")
        total_dist = validate_non_negative_float(total_train_distance, "Total Train Distance (km)")
        if total_dist < seg_dist:
            raise ValueError("Total Train Distance cannot be smaller than Segment Distance.")
        total_stops = validate_positive_int(total_train_stops, "Total Train Stops", min_val=2)
        stop_idx = validate_positive_int(stop_order_index, "Stop Order Index", min_val=1)
        if stop_idx >= total_stops:
            raise ValueError("Stop Order Index for a departing leg must be < Total Train Stops.")
        dep_hour = validate_positive_int(departure_hour, "Departure Hour", min_val=0)
        if dep_hour > 23:
            raise ValueError("Departure Hour must be between 0 and 23.")
        halt_min = validate_non_negative_float(halt_duration_minutes, "Halt Duration (minutes)")

        return PredictionInput(
            segment_distance=seg_dist,
            total_train_distance=total_dist,
            total_train_stops=total_stops,
            stop_order_index=stop_idx,
            departure_hour=dep_hour,
            halt_duration_minutes=halt_min,
        )

    def predict_leg_duration(self, validated_input: PredictionInput) -> float:
        """Predict scheduled travel duration in minutes for one route segment."""
        X_pred = validated_input.to_dataframe(self.feature_columns)
        prediction = float(self.model.predict(X_pred)[0])
        return round(max(1.0, prediction), 2)

    @staticmethod
    def load_metrics_report(metrics_path: Path | None = None) -> dict[str, Any]:
        """Load saved model comparison metrics JSON for dashboard visualization."""
        target = Path(metrics_path) if metrics_path else PATHS.model_metrics_path
        if not target.exists():
            return {}
        return json.loads(target.read_text(encoding="utf-8"))
