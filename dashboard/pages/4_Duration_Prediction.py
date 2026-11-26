
"""Page 4: ML Journey Duration Prediction and Model Evaluation Dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from database.connection import DatabaseConnectionError
from database.repository import RailwayRepository
from dashboard.data_loader import get_cached_predictor, get_mysql_status
from dashboard.styles import render_hero
from models.predictor import JourneyDurationPredictor


render_hero(
    "Journey Duration Prediction",
    "Estimate scheduled train segment duration using machine learning models",
)

st.markdown(
    """
    <div class="info-card">
        <strong>Project Scope:</strong> This model predicts scheduled
        station-to-station journey duration using timetable and route features.
        It does not predict live train delays because the dataset does not contain
        verified historical real-time delay records.
    </div>
    """,
    unsafe_allow_html=True,
)

predictor = get_cached_predictor()
metrics_report = JourneyDurationPredictor.load_metrics_report()

# Prediction form and model information
col_form, col_info = st.columns([1.3, 1])

with col_form:
    st.subheader("🚆 Predict Journey Duration")
    st.write("Enter the train segment details below.")

    with st.form("prediction_form"):
        f1, f2 = st.columns(2)

        with f1:
            segment_distance = st.number_input(
                "Segment Distance (km)",
                min_value=1.0,
                max_value=2000.0,
                value=85.0,
                step=5.0,
            )

            total_train_distance = st.number_input(
                "Total Train Distance (km)",
                min_value=1.0,
                max_value=5000.0,
                value=950.0,
                step=25.0,
            )

            total_train_stops = st.number_input(
                "Total Stops",
                min_value=2,
                max_value=150,
                value=18,
                step=1,
            )

        with f2:
            stop_order_index = st.number_input(
                "Current Stop Index",
                min_value=1,
                max_value=149,
                value=4,
                step=1,
            )

            departure_hour = st.slider(
                "Departure Hour (24-hour format)",
                min_value=0,
                max_value=23,
                value=14,
            )

            halt_duration_minutes = st.number_input(
                "Station Halt Duration (minutes)",
                min_value=0.0,
                max_value=180.0,
                value=5.0,
                step=1.0,
            )

        st.divider()

        optional_train_no = st.number_input(
            "Train Number (Optional)",
            min_value=0,
            value=0,
            step=1,
            help="Enter 0 if you do not want to associate this prediction with a train.",
        )

        save_to_db = st.checkbox(
            "Save prediction to MySQL",
            value=True,
        )

        submitted = st.form_submit_button(
            "Predict Journey Duration",
            type="primary",
            use_container_width=True,
        )

with col_info:
    st.subheader("🤖 Active ML Model")

    st.metric(
        "Selected Best Model",
        predictor.model_name,
    )

    if predictor.metrics:
        st.markdown("### Model Performance")

        m1, m2, m3 = st.columns(3)

        m1.metric(
            "MAE",
            f"{predictor.metrics.get('mae', 0):.2f}",
            help="Mean Absolute Error in minutes. Lower is better.",
        )

        m2.metric(
            "RMSE",
            f"{predictor.metrics.get('rmse', 0):.2f}",
            help="Root Mean Squared Error in minutes. Lower is better.",
        )

        m3.metric(
            "R² Score",
            f"{predictor.metrics.get('r2', 0):.3f}",
            help="Coefficient of determination. Higher is generally better.",
        )

    st.markdown("### Prediction Information")

    st.markdown(
        """
        - **Input:** Distance, stops, departure hour and halt duration.
        - **Output:** Estimated scheduled segment duration.
        - **Unit:** Minutes.
        - **Purpose:** Estimate travel time between consecutive stations.
        """
    )

# Prediction result
if submitted:
    st.divider()
    st.subheader("📊 Prediction Result")

    try:
        if segment_distance > total_train_distance:
            raise ValueError(
                "Segment distance cannot exceed total train distance."
            )

        if stop_order_index >= total_train_stops:
            raise ValueError(
                "Current stop index must be smaller than the total number of stops."
            )

        validated = predictor.validate_inputs(
            segment_distance=segment_distance,
            total_train_distance=total_train_distance,
            total_train_stops=int(total_train_stops),
            stop_order_index=int(stop_order_index),
            departure_hour=int(departure_hour),
            halt_duration_minutes=halt_duration_minutes,
        )

        pred_min = float(predictor.predict_leg_duration(validated))

        if not pd.notna(pred_min) or pred_min <= 0:
            raise ValueError(
                "The model returned an invalid duration. Please check the inputs."
            )

        hrs = int(pred_min // 60)
        rem_min = pred_min % 60

        implied_speed = (
            round(segment_distance / (pred_min / 60.0), 1)
            if pred_min > 0
            else 0.0
        )

        result_col1, result_col2 = st.columns(2)

        with result_col1:
            st.markdown(
                f"""
                <div class="prediction-result">
                    <div>Estimated Scheduled Duration</div>
                    <h2>{pred_min:.1f} minutes</h2>
                    <div>{hrs} hours and {rem_min:.0f} minutes</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with result_col2:
            st.metric(
                "Estimated Average Segment Speed",
                f"{implied_speed} km/h",
            )

            st.metric(
                "Segment Distance",
                f"{segment_distance:.1f} km",
            )

        st.caption(
            "This is a model-based estimate, not a confirmed railway schedule "
            "or live operational prediction."
        )

        # Optional MySQL prediction history
        if save_to_db:
            db_ok, db_msg = get_mysql_status()

            if db_ok:
                try:
                    repo = RailwayRepository()

                    pid = repo.log_prediction(
                        segment_distance=validated.segment_distance,
                        total_train_distance=validated.total_train_distance,
                        total_train_stops=validated.total_train_stops,
                        stop_order_index=validated.stop_order_index,
                        departure_hour=validated.departure_hour,
                        halt_duration_minutes=validated.halt_duration_minutes,
                        predicted_duration_minutes=pred_min,
                        model_name=predictor.model_name,
                        train_no=(
                            int(optional_train_no)
                            if optional_train_no > 0
                            else None
                        ),
                    )

                    st.success(
                        f"Prediction #{pid} successfully saved to MySQL."
                    )

                except DatabaseConnectionError as exc:
                    st.warning(
                        f"Prediction completed, but MySQL logging failed: {exc}"
                    )

            else:
                st.info(
                    f"Prediction completed successfully. "
                    f"MySQL logging skipped: {db_msg}"
                )

    except ValueError as exc:
        st.error(f"Please check your inputs: {exc}")

# Model evaluation
st.divider()
st.subheader("📈 Model Comparison & Evaluation")

if metrics_report and metrics_report.get("models"):
    models_df = pd.DataFrame(metrics_report["models"])

    st.markdown("### Model Performance Comparison")

    st.dataframe(
        models_df,
        use_container_width=True,
        hide_index=True,
    )

    c1, c2 = st.columns(2)

    # MAE and RMSE comparison
    with c1:
        error_columns = [
            col for col in ["mae", "rmse"]
            if col in models_df.columns
        ]

        if "model_name" in models_df.columns and error_columns:
            melted = models_df.melt(
                id_vars="model_name",
                value_vars=error_columns,
                var_name="Metric",
                value_name="Error (Minutes)",
            )

            fig_err = px.bar(
                melted,
                x="model_name",
                y="Error (Minutes)",
                color="Metric",
                barmode="group",
                title="Model Error Comparison (Lower is Better)",
                labels={"model_name": "Regression Model"},
                color_discrete_sequence=["#2563eb", "#0891b2"],
            )

            fig_err.update_layout(
                template="plotly_white",
                height=380,
                xaxis_tickangle=-25,
            )

            st.plotly_chart(fig_err, use_container_width=True)

    # R2 comparison
    with c2:
        if "model_name" in models_df.columns and "r2" in models_df.columns:
            fig_r2 = px.bar(
                models_df,
                x="model_name",
                y="r2",
                color="model_name",
                title="R² Score Comparison (Higher is Better)",
                labels={
                    "model_name": "Regression Model",
                    "r2": "R² Score",
                },
                color_discrete_sequence=px.colors.qualitative.Set2,
            )

            fig_r2.update_layout(
                template="plotly_white",
                showlegend=False,
                height=380,
                xaxis_tickangle=-25,
            )

            st.plotly_chart(fig_r2, use_container_width=True)

    # Feature importance and sample predictions
    c3, c4 = st.columns(2)

    with c3:
        feature_importance = metrics_report.get("feature_importance", {})

        if feature_importance:
            fi_df = pd.DataFrame(
                {
                    "Feature": list(feature_importance.keys()),
                    "Importance": list(feature_importance.values()),
                }
            ).sort_values("Importance", ascending=True)

            fig_fi = px.bar(
                fi_df,
                x="Importance",
                y="Feature",
                orientation="h",
                title=(
                    "Feature Importance "
                    f"({metrics_report.get('best_model', 'Best Model')})"
                ),
                color_discrete_sequence=["#087eaa"],
            )

            fig_fi.update_layout(
                template="plotly_white",
                height=380,
            )

            st.plotly_chart(fig_fi, use_container_width=True)
        else:
            st.info("Feature importance information is not available.")

    with c4:
        samples = metrics_report.get("sample_predictions", {})

        if samples and samples.get("actual") and samples.get("predicted"):
            scatter_df = pd.DataFrame(samples)

            if {"actual", "predicted"}.issubset(scatter_df.columns):
                scatter_df = scatter_df.dropna(
                    subset=["actual", "predicted"]
                )

                if not scatter_df.empty:
                    fig_scat = px.scatter(
                        scatter_df,
                        x="actual",
                        y="predicted",
                        opacity=0.65,
                        title="Actual vs Predicted Duration",
                        labels={
                            "actual": "Actual Duration (minutes)",
                            "predicted": "Predicted Duration (minutes)",
                        },
                    )

                    max_val = max(
                        scatter_df["actual"].max(),
                        scatter_df["predicted"].max(),
                    )

                    fig_scat.add_shape(
                        type="line",
                        x0=0,
                        y0=0,
                        x1=max_val,
                        y1=max_val,
                        line=dict(color="#ef4444", dash="dash"),
                    )

                    fig_scat.update_layout(
                        template="plotly_white",
                        height=380,
                    )

                    st.plotly_chart(fig_scat, use_container_width=True)
        else:
            st.info("Sample prediction data is not available.")

else:
    st.warning(
        "Model evaluation report is not available. "
        "Please check whether the ML training pipeline has generated its metrics report."
    )

# MySQL prediction history
db_ok, db_msg = get_mysql_status()

if db_ok:
    st.divider()
    st.subheader("🗄️ Recent Prediction History")

    try:
        history = RailwayRepository().get_prediction_history(limit=20)

        if history:
            st.dataframe(
                pd.DataFrame(history),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No predictions have been saved yet.")

    except DatabaseConnectionError as exc:
        st.warning(f"Unable to retrieve prediction history: {exc}")

else:
    st.caption(
        "MySQL prediction history is currently unavailable because the database "
        "is not configured or running."
    )
