"""Page 3: Railway Route Analysis — longest/shortest routes, busiest stations, and route profile."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from analytics.route_analysis import (
    get_busiest_stations,
    get_longest_and_shortest_routes,
    get_train_route_profile,
)
from dashboard.data_loader import load_dashboard_datasets
from dashboard.styles import render_hero

render_hero(
    "Train Route Analysis",
    "Compare longest and shortest rail corridors, station traffic density, and stop-by-stop train profiles",
)

features_df, train_summary_df, station_summary_df = load_dashboard_datasets()

top_n = st.slider("Number of Top Routes / Stations to Display", min_value=5, max_value=25, value=10)
longest_df, shortest_df = get_longest_and_shortest_routes(train_summary_df, top_n=top_n)

col1, col2 = st.columns(2)
with col1:
    longest_plot = longest_df.copy()
    longest_plot["Route_Label"] = (
        longest_plot["Train_No"].astype(str)
        + " ("
        + longest_plot["Origin_Code"]
        + "→"
        + longest_plot["Destination_Code"]
        + ")"
    )
    fig_long = px.bar(
        longest_plot.sort_values("Total_Distance", ascending=True),
        x="Total_Distance",
        y="Route_Label",
        orientation="h",
        color="Number_of_Stops",
        title=f"Top {top_n} Longest Train Routes (km)",
        labels={"Total_Distance": "Total Distance (km)", "Route_Label": "Train Route"},
        color_continuous_scale="Blues",
    )
    fig_long.update_layout(template="plotly_white", height=420)
    st.plotly_chart(fig_long, use_container_width=True)

with col2:
    shortest_plot = shortest_df.copy()
    shortest_plot["Route_Label"] = (
        shortest_plot["Train_No"].astype(str)
        + " ("
        + shortest_plot["Origin_Code"]
        + "→"
        + shortest_plot["Destination_Code"]
        + ")"
    )
    fig_short = px.bar(
        shortest_plot.sort_values("Total_Distance", ascending=False),
        x="Total_Distance",
        y="Route_Label",
        orientation="h",
        color="Number_of_Stops",
        title=f"Top {top_n} Shortest Train Routes (km)",
        labels={"Total_Distance": "Total Distance (km)", "Route_Label": "Train Route"},
        color_continuous_scale="YlOrBr",
    )
    fig_short.update_layout(template="plotly_white", height=420)
    st.plotly_chart(fig_short, use_container_width=True)

st.subheader("Busiest Stations Breakdown")
busiest_df = get_busiest_stations(station_summary_df, top_n=top_n)
fig_stations = px.bar(
    busiest_df,
    x="Station_Code",
    y=["Origin_Train_Count", "Destination_Train_Count", "Total_Train_Visits"],
    barmode="group",
    title=f"Top {top_n} Busiest Stations: Origins, Destinations & Total Visits",
    labels={"value": "Number of Trains", "Station_Code": "Station Code", "variable": "Metric"},
)
fig_stations.update_layout(template="plotly_white", height=380)
st.plotly_chart(fig_stations, use_container_width=True)

st.divider()
st.subheader("Single-Train Route Deep Dive")
train_options = train_summary_df.sort_values("Total_Distance", ascending=False)["Train_No"].head(300).tolist()
selected_train = st.selectbox("Select a Train Number to Inspect Route Profile", options=train_options)
profile_df = get_train_route_profile(features_df, selected_train)

if not profile_df.empty:
    p1, p2 = st.columns(2)
    with p1:
        leg_df = profile_df.dropna(subset=["Journey_Duration_Minutes"])
        fig_leg = px.bar(
            leg_df,
            x="Station_Name",
            y="Journey_Duration_Minutes",
            color="Segment_Distance",
            title=f"Leg-by-Leg Scheduled Duration — Train {selected_train}",
            labels={
                "Station_Name": "Departing Station",
                "Journey_Duration_Minutes": "Leg Duration (min)",
            },
        )
        fig_leg.update_layout(template="plotly_white", xaxis_tickangle=-45, height=380)
        st.plotly_chart(fig_leg, use_container_width=True)

    with p2:
        fig_fare = px.line(
            profile_df,
            x="Distance",
            y=["1A", "2A", "3A", "SL"],
            markers=True,
            title=f"Fare Progression by Distance — Train {selected_train}",
            labels={"Distance": "Cumulative Distance (km)", "value": "Fare (INR)", "variable": "Class"},
        )
        fig_fare.update_layout(template="plotly_white", height=380)
        st.plotly_chart(fig_fare, use_container_width=True)
