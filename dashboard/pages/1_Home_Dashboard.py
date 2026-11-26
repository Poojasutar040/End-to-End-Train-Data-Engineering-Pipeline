"""Page 1: Home Dashboard with KPIs, interactive Plotly charts, and quick train lookup."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from analytics.route_analysis import get_busiest_stations
from analytics.search import search_by_train_number
from dashboard.data_loader import get_cached_kpis, load_dashboard_datasets
from dashboard.styles import render_hero, render_kpi_card

render_hero(
    "Smart Railway Analytics & Train Journey Prediction System",
    "Interactive Data Engineering, Route Intelligence, MySQL Integration, and ML Scheduled Duration Estimation",
)

features_df, train_summary_df, station_summary_df = load_dashboard_datasets()
kpis = get_cached_kpis()

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card("Total Trains", f"{kpis['total_trains']:,}", "Unique scheduled trains")
with col2:
    render_kpi_card("Total Stations", f"{kpis['total_stations']:,}", "Standardized station codes")
with col3:
    render_kpi_card(
        "Total Routes",
        f"{kpis['total_routes']:,}",
        f"{kpis['total_route_segments']:,} station-to-station legs",
    )
with col4:
    render_kpi_card(
        "Avg Journey Duration",
        f"{kpis['avg_journey_duration_hours']:.1f} hrs",
        f"{kpis['avg_journey_duration_min']:.1f} min total | {kpis['avg_leg_duration_min']:.1f} min/leg",
    )

st.markdown("#### Quick Train Schedule Lookup")
search_col, btn_col = st.columns([3, 1])
with search_col:
    sample_train = int(train_summary_df["Train_No"].iloc[0])
    quick_train_no = st.number_input(
        "Enter Train Number",
        min_value=1,
        value=sample_train,
        step=1,
        key="home_quick_train",
    )
with btn_col:
    st.write("")
    st.write("")
    lookup_clicked = st.button("Lookup Schedule", type="primary", use_container_width=True)

if lookup_clicked:
    schedule = search_by_train_number(features_df, quick_train_no)
    if schedule.empty:
        st.warning(f"No train found with Train Number {quick_train_no}.")
    else:
        st.success(
            f"Train {quick_train_no}: {schedule.iloc[0]['Station_Name']} ({schedule.iloc[0]['Station_Code']}) "
            f"→ {schedule.iloc[-1]['Station_Name']} ({schedule.iloc[-1]['Station_Code']}) | "
            f"{len(schedule)} stops | {schedule.iloc[-1]['Distance']:,} km"
        )
        display_cols = [
            "SN",
            "Station_Code",
            "Station_Name",
            "Arrival_time",
            "Departure_Time",
            "Distance",
            "Journey_Duration_Minutes",
        ]
        st.dataframe(schedule[display_cols], use_container_width=True, hide_index=True)

st.divider()

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    fig_stops = px.histogram(
        train_summary_df,
        x="Number_of_Stops",
        nbins=35,
        title="Distribution of Number of Stops per Train",
        labels={"Number_of_Stops": "Stops per Train", "count": "Train Count"},
        color_discrete_sequence=["#1d4ed8"],
    )
    fig_stops.update_layout(template="plotly_white", height=380)
    st.plotly_chart(fig_stops, use_container_width=True)

with chart_col2:
    fig_dist = px.histogram(
        train_summary_df,
        x="Total_Distance",
        nbins=35,
        title="Distribution of Total Route Distance (km)",
        labels={"Total_Distance": "Total Distance (km)", "count": "Train Count"},
        color_discrete_sequence=["#0284c7"],
    )
    fig_dist.update_layout(template="plotly_white", height=380)
    st.plotly_chart(fig_dist, use_container_width=True)

busiest = get_busiest_stations(station_summary_df, top_n=12)
fig_busiest = px.bar(
    busiest.sort_values("Total_Train_Visits", ascending=True),
    x="Total_Train_Visits",
    y="Station_Name",
    orientation="h",
    color="Total_Train_Visits",
    color_continuous_scale="Blues",
    title="Top 12 Busiest Railway Stations (by Train Visits)",
    labels={"Total_Train_Visits": "Unique Trains Stopping", "Station_Name": "Station"},
    hover_data=["Station_Code", "Origin_Train_Count", "Destination_Train_Count"],
)
fig_busiest.update_layout(template="plotly_white", height=430, coloraxis_showscale=False)
st.plotly_chart(fig_busiest, use_container_width=True)
