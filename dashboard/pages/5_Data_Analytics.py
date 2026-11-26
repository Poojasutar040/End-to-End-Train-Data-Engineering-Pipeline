
"""Page 5: Railway Data Analytics and MySQL CRUD Management."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from database.connection import DatabaseConnectionError
from database.repository import RailwayRepository
from dashboard.data_loader import get_mysql_status, load_dashboard_datasets
from dashboard.styles import render_hero


render_hero(
    "Railway Data Analytics",
    "Explore railway network patterns, train distances, scheduled speeds, fares and database records",
)

features_df, train_summary_df, station_summary_df = load_dashboard_datasets()

# Overview
st.subheader("Railway Network Overview")

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Trains", f"{len(train_summary_df):,}")
k2.metric("Total Stations", f"{len(station_summary_df):,}")
k3.metric("Total Schedule Records", f"{len(features_df):,}")

if "Total_Distance" in train_summary_df.columns:
    avg_distance = train_summary_df["Total_Distance"].mean()
    k4.metric(
        "Average Train Distance",
        f"{avg_distance:,.1f} km" if pd.notna(avg_distance) else "N/A",
    )
else:
    k4.metric("Average Train Distance", "N/A")

st.caption(
    "Analytics are calculated from the available railway timetable dataset. "
    "They do not represent live railway operations."
)

tab_charts, tab_db = st.tabs(
    ["📊 Network Analytics", "🗄️ MySQL Database Management"]
)

# --------------------------------------------------
# TAB 1: NETWORK ANALYTICS
# --------------------------------------------------
with tab_charts:
    st.subheader("Railway Network Insights")

    c1, c2 = st.columns(2)

    # Scheduled departures by hour
    with c1:
        if "Departure_Hour" in features_df.columns:
            hourly = (
                features_df.groupby("Departure_Hour")
                .size()
                .reset_index(name="Departures")
                .sort_values("Departure_Hour")
            )

            fig_hour = px.bar(
                hourly,
                x="Departure_Hour",
                y="Departures",
                title="Scheduled Departures by Hour",
                labels={
                    "Departure_Hour": "Hour of Day",
                    "Departures": "Number of Departures",
                },
                color="Departures",
                color_continuous_scale="Blues",
            )

            fig_hour.update_layout(
                template="plotly_white",
                height=390,
                coloraxis_showscale=False,
                xaxis=dict(dtick=1),
            )

            st.plotly_chart(fig_hour, use_container_width=True)
        else:
            st.info("Departure hour information is unavailable.")

    # Train distance categories
    with c2:
        if "Total_Distance" in train_summary_df.columns:
            distance_data = train_summary_df[
                ["Total_Distance"]
            ].dropna()

            bands = pd.cut(
                distance_data["Total_Distance"],
                bins=[-1, 100, 500, 1500, float("inf")],
                labels=[
                    "Short (under 100 km)",
                    "Medium (100–500 km)",
                    "Long (500–1500 km)",
                    "Ultra-long (over 1500 km)",
                ],
            )

            band_counts = (
                bands.value_counts(sort=False)
                .reset_index()
            )

            band_counts.columns = ["Distance Category", "Train Count"]

            fig_distance = px.pie(
                band_counts,
                names="Distance Category",
                values="Train Count",
                hole=0.45,
                title="Train Distribution by Distance",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )

            fig_distance.update_layout(
                template="plotly_white",
                height=390,
            )

            st.plotly_chart(fig_distance, use_container_width=True)
        else:
            st.info("Train distance information is unavailable.")

    c3, c4 = st.columns(2)

    # Segment speed distribution
    with c3:
        if "Segment_Speed_Kmph" in features_df.columns:
            valid_legs = features_df[
                features_df["Segment_Speed_Kmph"].between(5, 140)
            ].dropna(subset=["Segment_Speed_Kmph"])

            if not valid_legs.empty:
                fig_speed = px.histogram(
                    valid_legs,
                    x="Segment_Speed_Kmph",
                    nbins=40,
                    title="Scheduled Segment Speed Distribution",
                    labels={
                        "Segment_Speed_Kmph": "Segment Speed (km/h)",
                        "count": "Number of Segments",
                    },
                    color_discrete_sequence=["#087eaa"],
                )

                fig_speed.update_layout(
                    template="plotly_white",
                    height=390,
                )

                st.plotly_chart(fig_speed, use_container_width=True)
            else:
                st.info("No valid segment speed records are available.")
        else:
            st.info("Segment speed information is unavailable.")

    # Fare versus distance
    with c4:
        fare_columns = [
            col for col in ["Max_1A_Fare", "Max_SL_Fare"]
            if col in train_summary_df.columns
        ]

        if "Total_Distance" in train_summary_df.columns and fare_columns:
            fare_sample = train_summary_df[
                ["Total_Distance"] + fare_columns
            ].dropna(subset=["Total_Distance"])

            fare_sample = fare_sample[
                fare_sample["Total_Distance"] > 0
            ].head(1500)

            if not fare_sample.empty:
                fare_long = fare_sample.melt(
                    id_vars="Total_Distance",
                    value_vars=fare_columns,
                    var_name="Travel Class",
                    value_name="Fare (INR)",
                ).dropna(subset=["Fare (INR)"])

                fare_long["Travel Class"] = fare_long[
                    "Travel Class"
                ].replace(
                    {
                        "Max_1A_Fare": "First AC",
                        "Max_SL_Fare": "Sleeper",
                    }
                )

                fig_fare = px.scatter(
                    fare_long,
                    x="Total_Distance",
                    y="Fare (INR)",
                    color="Travel Class",
                    opacity=0.6,
                    title="Fare versus Train Route Distance",
                    labels={
                        "Total_Distance": "Total Distance (km)",
                    },
                    color_discrete_sequence=["#2563eb", "#0891b2"],
                )

                fig_fare.update_layout(
                    template="plotly_white",
                    height=390,
                )

                st.plotly_chart(fig_fare, use_container_width=True)
            else:
                st.info("Fare analysis data is unavailable.")
        else:
            st.info("Required fare or distance columns are unavailable.")

    # Additional summary
    st.divider()
    st.subheader("Additional Network Statistics")

    if "Total_Distance" in train_summary_df.columns:
        distances = train_summary_df["Total_Distance"].dropna()

        if not distances.empty:
            s1, s2, s3 = st.columns(3)

            s1.metric("Longest Train Route", f"{distances.max():,.1f} km")
            s2.metric("Shortest Train Route", f"{distances.min():,.1f} km")
            s3.metric("Median Route Distance", f"{distances.median():,.1f} km")

# --------------------------------------------------
# TAB 2: MYSQL DATABASE MANAGEMENT
# --------------------------------------------------
with tab_db:
    st.subheader("MySQL Database Operations")

    db_ok, db_msg = get_mysql_status()

    if not db_ok:
        st.warning(f"MySQL is currently unavailable: {db_msg}")

        st.markdown(
            """
            **Steps to enable MySQL integration:**

            1. Install and start MySQL Server 8.0.
            2. Create your project `.env` file using `.env.example`.
            3. Configure the database name, username and password.
            4. Run the project's database initialization process.
            5. Refresh this page to check the connection.

            Keep your database password private. Do not share your `.env` file.
            """
        )

    else:
        st.success(db_msg)

        try:
            repo = RailwayRepository()

            st.markdown("### Station CRUD Operations")

            st.caption(
                "Manage station records stored in the MySQL database."
            )

            crud_col1, crud_col2 = st.columns(2)

            # CREATE / UPDATE
            with crud_col1:
                with st.form("station_upsert_form"):
                    st.markdown("#### Create or Update Station")

                    s_code = st.text_input(
                        "Station Code",
                        value="DEMO1",
                        max_chars=10,
                    )

                    s_name = st.text_input(
                        "Station Name",
                        value="DEMO JUNCTION",
                        max_chars=150,
                    )

                    save_station = st.form_submit_button(
                        "Save Station",
                        type="primary",
                        use_container_width=True,
                    )

                if save_station:
                    try:
                        if not s_code.strip() or not s_name.strip():
                            st.warning("Please enter both station code and station name.")
                        else:
                            repo.create_station(
                                s_code.strip(),
                                s_name.strip(),
                            )

                            st.success(
                                f"Station {s_code.upper()} saved successfully."
                            )

                    except (ValueError, DatabaseConnectionError) as exc:
                        st.error(str(exc))

            # READ / DELETE
            with crud_col2:
                with st.form("station_lookup_delete_form"):
                    st.markdown("#### Read or Delete Station")

                    q_code = st.text_input(
                        "Target Station Code",
                        value="DEMO1",
                        max_chars=10,
                    )

                    action = st.radio(
                        "Select Operation",
                        ["Read", "Delete"],
                        horizontal=True,
                    )

                    confirm_delete = False

                    if action == "Delete":
                        confirm_delete = st.checkbox(
                            "I confirm that I want to delete this station."
                        )

                    execute = st.form_submit_button(
                        "Execute Operation",
                        use_container_width=True,
                    )

                if execute:
                    try:
                        if not q_code.strip():
                            st.warning("Please enter a station code.")

                        elif action == "Read":
                            row = repo.get_station(q_code.strip())

                            if row:
                                st.success("Station record found.")
                                st.json(row)
                            else:
                                st.info("Station not found.")

                        elif action == "Delete":
                            if not confirm_delete:
                                st.warning("Please confirm before deleting a station.")
                            else:
                                deleted = repo.delete_station(q_code.strip())

                                if deleted:
                                    st.success(
                                        f"Deleted {deleted} station record(s)."
                                    )
                                else:
                                    st.info("No matching station record was found.")

                    except (ValueError, DatabaseConnectionError) as exc:
                        st.error(str(exc))

        except DatabaseConnectionError as exc:
            st.error(f"Unable to initialize MySQL repository: {exc}")
