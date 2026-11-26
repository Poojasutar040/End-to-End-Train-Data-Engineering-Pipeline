
"""Page 2: Interactive Train Search by Train Number, Station, or Route."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from analytics.search import (
    search_between_stations,
    search_by_station,
    search_by_train_number,
)
from dashboard.data_loader import load_dashboard_datasets
from dashboard.styles import render_hero


render_hero(
    "Train & Station Search",
    "Explore train timetables, station details and direct train connections",
)

features_df, train_summary_df, station_summary_df = load_dashboard_datasets()

st.caption(
    "Search results are based on the available railway timetable dataset. "
    "This application does not provide live train tracking."
)

tab1, tab2, tab3 = st.tabs(
    [
        "🚆 Train Number Search",
        "📍 Station Search",
        "🗺️ Between Stations",
    ]
)

# TAB 1: Search by Train Number
with tab1:
    st.subheader("Search Complete Train Timetable")
    st.write("Enter a train number or select a sample train to view its complete schedule.")

    sample_trains = train_summary_df["Train_No"].dropna().head(200).tolist()

    if not sample_trains:
        st.warning("No train records are available in the dataset.")
    else:
        col1, col2 = st.columns([2, 1])

        with col1:
            train_no_input = st.number_input(
                "Train Number",
                min_value=1,
                value=int(sample_trains[0]),
                step=1,
                key="search_train_no",
            )

        with col2:
            quick_pick = st.selectbox(
                "Sample Train",
                options=sample_trains,
                format_func=lambda x: str(int(x)),
                key="quick_pick_train",
            )

        use_pick = st.checkbox("Use selected sample train")
        target_train = int(quick_pick if use_pick else train_no_input)

        if st.button("Search Train", type="primary", key="search_train_button"):
            try:
                train_df = search_by_train_number(features_df, target_train)

                if train_df.empty:
                    st.warning(f"No timetable found for train {target_train}.")
                else:
                    summary_matches = train_summary_df[
                        train_summary_df["Train_No"] == target_train
                    ]

                    if summary_matches.empty:
                        st.warning("Train timetable found, but summary information is unavailable.")
                    else:
                        summary_row = summary_matches.iloc[0]

                        st.success(f"Timetable found for Train {target_train}")

                        st.markdown("### Train Overview")

                        m1, m2, m3, m4 = st.columns(4)

                        m1.metric(
                            "Starting Station",
                            f"{summary_row['Origin_Name']} ({summary_row['Origin_Code']})",
                        )

                        m2.metric(
                            "Destination",
                            f"{summary_row['Destination_Name']} ({summary_row['Destination_Code']})",
                        )

                        m3.metric(
                            "Total Stops",
                            f"{int(summary_row['Number_of_Stops'])}",
                        )

                        m4.metric(
                            "Total Distance",
                            f"{int(summary_row['Total_Distance']):,} km",
                        )

                        st.info(
                            "Scheduled journey duration: "
                            f"{summary_row['Total_Journey_Duration_Minutes']:.0f} minutes"
                        )

                        st.markdown("### Complete Train Timetable")

                        display_columns = [
                            "SN",
                            "Station_Code",
                            "Station_Name",
                            "Arrival_time",
                            "Departure_Time",
                            "Halt_Duration_Minutes",
                            "Distance",
                            "Segment_Distance",
                            "Journey_Duration_Minutes",
                            "1A",
                            "2A",
                            "3A",
                            "SL",
                        ]

                        available_columns = [
                            col for col in display_columns if col in train_df.columns
                        ]

                        st.dataframe(
                            train_df[available_columns],
                            use_container_width=True,
                            hide_index=True,
                        )

                        if "Distance" in train_df.columns and "Station_Name" in train_df.columns:
                            st.markdown("### Route Distance Progress")

                            fig = px.line(
                                train_df,
                                x="Station_Name",
                                y="Distance",
                                markers=True,
                                title=f"Distance Covered by Train {target_train}",
                                labels={
                                    "Station_Name": "Stations",
                                    "Distance": "Cumulative Distance (km)",
                                },
                            )

                            fig.update_traces(
                                line=dict(width=3),
                                marker=dict(size=8),
                            )

                            fig.update_layout(
                                template="plotly_white",
                                height=420,
                                xaxis_tickangle=-35,
                                margin=dict(l=20, r=20, t=60, b=80),
                            )

                            st.plotly_chart(fig, use_container_width=True)

            except (ValueError, KeyError) as exc:
                st.error(f"Unable to retrieve train timetable: {exc}")

# TAB 2: Search by Station
with tab2:
    st.subheader("Find Trains at a Station")

    st.write(
        "Enter a station code or station name to find trains that stop there."
    )

    station_query = st.text_input(
        "Station Code or Name",
        value="PUNE",
        placeholder="Example: PUNE, MAO, CSMT",
        key="station_search_input",
    )

    if st.button("Search Station", type="primary", key="search_station_button"):
        if not station_query.strip():
            st.warning("Please enter a station code or name.")
        else:
            try:
                station_matches = search_by_station(
                    features_df,
                    station_query.strip(),
                )

                if station_matches.empty:
                    st.warning(f"No trains found for '{station_query}'.")
                else:
                    st.success(
                        f"Found {len(station_matches):,} station records "
                        f"across {station_matches['Train_No'].nunique():,} trains."
                    )

                    st.metric(
                        "Total Matching Trains",
                        f"{station_matches['Train_No'].nunique():,}",
                    )

                    st.markdown("### Matching Train Details")

                    st.dataframe(
                        station_matches.head(500),
                        use_container_width=True,
                        hide_index=True,
                    )

                    if len(station_matches) > 500:
                        st.caption(
                            "Showing the first 500 matching records."
                        )

            except (ValueError, KeyError) as exc:
                st.error(f"Unable to search station: {exc}")

# TAB 3: Search Between Stations
with tab3:
    st.subheader("Find Direct Train Connections")

    st.write(
        "Enter the starting and destination station codes or names "
        "to find trains connecting both stations."
    )

    col_a, col_b = st.columns(2)

    with col_a:
        origin_q = st.text_input(
            "Origin Station",
            value="SWV",
            placeholder="Example: SWV",
            key="origin_station",
        )

    with col_b:
        dest_q = st.text_input(
            "Destination Station",
            value="MAO",
            placeholder="Example: MAO",
            key="destination_station",
        )

    if st.button("Find Direct Trains", type="primary"):
        if not origin_q.strip() or not dest_q.strip():
            st.warning("Please enter both origin and destination stations.")

        elif origin_q.strip().lower() == dest_q.strip().lower():
            st.warning("Origin and destination stations must be different.")

        else:
            try:
                od_df = search_between_stations(
                    features_df,
                    origin_q.strip(),
                    dest_q.strip(),
                )

                if od_df.empty:
                    st.warning(
                        f"No direct train connections found from "
                        f"'{origin_q}' to '{dest_q}'."
                    )
                else:
                    st.success(
                        f"Found {len(od_df):,} direct train connection(s)."
                    )

                    st.markdown("### Available Train Connections")

                    st.dataframe(
                        od_df,
                        use_container_width=True,
                        hide_index=True,
                    )

            except (ValueError, KeyError) as exc:
                st.error(f"Unable to find train connections: {exc}")
