"""Page 6: Report generation and CSV / Markdown downloads."""

from __future__ import annotations

import streamlit as st

from analytics.route_analysis import get_busiest_stations, get_longest_and_shortest_routes
from dashboard.data_loader import get_cached_kpis, load_dashboard_datasets
from dashboard.styles import render_hero
from models.predictor import JourneyDurationPredictor
from reports.generator import export_route_summary_csv, generate_markdown_summary_report

render_hero(
    "Reports & Data Exports",
    "Filter route datasets and download executive Markdown and CSV reports for documentation and review",
)

features_df, train_summary_df, station_summary_df = load_dashboard_datasets()
kpis = get_cached_kpis()
ml_metrics = JourneyDurationPredictor.load_metrics_report()

st.subheader("Filter Train Routes for Export")
c1, c2 = st.columns(2)
with c1:
    min_distance = st.slider(
        "Minimum Total Distance (km)",
        min_value=0,
        max_value=int(train_summary_df["Total_Distance"].max()),
        value=100,
        step=50,
    )
with c2:
    min_stops = st.slider(
        "Minimum Number of Stops",
        min_value=1,
        max_value=int(train_summary_df["Number_of_Stops"].max()),
        value=5,
        step=1,
    )

filtered_routes = train_summary_df[
    (train_summary_df["Total_Distance"] >= min_distance)
    & (train_summary_df["Number_of_Stops"] >= min_stops)
].sort_values("Total_Distance", ascending=False)

st.info(f"Filtered dataset contains **{len(filtered_routes):,}** trains.")
st.dataframe(filtered_routes.head(200), use_container_width=True, hide_index=True)

st.divider()
st.subheader("Generate & Download Reports")

longest_routes, _ = get_longest_and_shortest_routes(train_summary_df, top_n=10)
busiest_stations = get_busiest_stations(station_summary_df, top_n=15)

dl1, dl2, dl3 = st.columns(3)

with dl1:
    csv_path = export_route_summary_csv(
        train_summary_df, min_distance=min_distance, min_stops=min_stops
    )
    st.download_button(
        label="Download Filtered Routes (CSV)",
        data=csv_path.read_bytes(),
        file_name="filtered_train_routes.csv",
        mime="text/csv",
        use_container_width=True,
    )

with dl2:
    md_path = generate_markdown_summary_report(
        kpis=kpis,
        longest_routes=longest_routes,
        busiest_stations=busiest_stations,
        ml_metrics=ml_metrics,
    )
    st.download_button(
        label="Download Executive Report (Markdown)",
        data=md_path.read_bytes(),
        file_name="railway_analytics_report.md",
        mime="text/markdown",
        use_container_width=True,
    )

with dl3:
    stations_csv = station_summary_df.sort_values("Total_Train_Visits", ascending=False).to_csv(
        index=False
    )
    st.download_button(
        label="Download Station Summary (CSV)",
        data=stations_csv.encode("utf-8"),
        file_name="station_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )
