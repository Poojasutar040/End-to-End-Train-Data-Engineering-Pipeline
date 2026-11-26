"""Generate System Architecture, DFD, and ER diagrams for MCA documentation."""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt

DIAGRAMS_DIR = Path(__file__).resolve().parent


def _draw_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    facecolor: str,
    edgecolor: str = "#1e293b",
    fontsize: int = 9,
    bold: bool = True,
) -> None:
    box = patches.FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.5,
    )
    ax.add_patch(box)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight="bold" if bold else "normal",
        color="#0f172a",
    )


def _draw_arrow(ax: plt.Axes, x1: float, y1: float, x2: float, y2: float, label: str = "") -> None:
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", lw=1.6, color="#334155"),
    )
    if label:
        ax.text(
            (x1 + x2) / 2,
            (y1 + y2) / 2 + 0.02,
            label,
            ha="center",
            va="bottom",
            fontsize=8,
            color="#334155",
        )


def create_system_architecture() -> None:
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("System Architecture — Smart Railway Analytics & Prediction System", fontsize=13, fontweight="bold", pad=12)

    # Layer 1: Presentation
    _draw_box(ax, 0.08, 0.78, 0.84, 0.14, "PRESENTATION LAYER (Streamlit + Plotly + Custom CSS)\nHome Dashboard | Train Search | Route Analysis | ML Prediction | Analytics | Reports | About", "#dbeafe", "#1d4ed8", 10)

    # Layer 2: Backend Services
    _draw_box(ax, 0.08, 0.50, 0.25, 0.16, "Analytics Engine\n(analytics/)\nKPIs, Search, OD Routes", "#e0f2fe", "#0284c7")
    _draw_box(ax, 0.375, 0.50, 0.25, 0.16, "ML Pipeline\n(models/)\nLR, DT, RF + Predictor", "#dcfce7", "#15803d")
    _draw_box(ax, 0.67, 0.50, 0.25, 0.16, "Report Generator\n(reports/)\nCSV & Markdown Exports", "#fef3c7", "#b45309")

    # Layer 3: ETL
    _draw_box(ax, 0.08, 0.26, 0.40, 0.14, "Data Ingestion & Cleaning\n(ingestion/, preprocessing/cleaner.py)\nSchema Check, Deduplication, Station Standardization", "#f1f5f9", "#475569")
    _draw_box(ax, 0.52, 0.26, 0.40, 0.14, "Transformation & Feature Engineering\n(preprocessing/transformer.py)\nSort (Train_No, SN), Segment Distance & Duration", "#f1f5f9", "#475569")

    # Layer 4: Storage
    _draw_box(ax, 0.08, 0.05, 0.40, 0.12, "CSV & Joblib Storage (data/, models/)\nRaw, Cleaned, Processed CSVs + .pkl", "#ede9fe", "#6d28d9")
    _draw_box(ax, 0.52, 0.05, 0.40, 0.12, "MySQL 8.0 Database (database/)\nstations, trains, schedules, routes, predictions", "#fee2e2", "#b91c1c")

    _draw_arrow(ax, 0.20, 0.78, 0.20, 0.66)
    _draw_arrow(ax, 0.50, 0.78, 0.50, 0.66)
    _draw_arrow(ax, 0.80, 0.78, 0.80, 0.66)
    _draw_arrow(ax, 0.48, 0.33, 0.52, 0.33)
    _draw_arrow(ax, 0.28, 0.26, 0.28, 0.17)
    _draw_arrow(ax, 0.72, 0.26, 0.72, 0.17)
    _draw_arrow(ax, 0.50, 0.40, 0.50, 0.50)

    fig.tight_layout()
    fig.savefig(DIAGRAMS_DIR / "system_architecture.png", dpi=200)
    plt.close(fig)


def create_data_flow_diagram() -> None:
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Data Flow Diagram (Level 1 DFD)", fontsize=13, fontweight="bold", pad=12)

    _draw_box(ax, 0.03, 0.62, 0.17, 0.18, "Raw CSV\ntrain_schedule.csv\n(186,074 rows)", "#f1f5f9")
    _draw_box(ax, 0.25, 0.62, 0.18, 0.18, "1.0 Ingestion\n& Cleaning\nDeduplicate & Fix Times", "#dbeafe")
    _draw_box(ax, 0.48, 0.62, 0.20, 0.18, "2.0 Transform\n& Feature Eng.\nSort (Train_No, SN)", "#dcfce7")
    _draw_box(ax, 0.74, 0.62, 0.22, 0.18, "3.0 Analytics &\nML Training\nLR / DT / RF", "#fef3c7")

    _draw_box(ax, 0.25, 0.15, 0.22, 0.18, "D1: Processed CSVs\n& Model (.pkl)", "#ede9fe")
    _draw_box(ax, 0.53, 0.15, 0.20, 0.18, "D2: MySQL 8.0\nRelational Tables", "#fee2e2")
    _draw_box(ax, 0.78, 0.15, 0.19, 0.18, "User / Reviewer\nStreamlit Dashboard\n& Reports", "#e0f2fe")

    _draw_arrow(ax, 0.20, 0.71, 0.25, 0.71, "Raw")
    _draw_arrow(ax, 0.43, 0.71, 0.48, 0.71, "Cleaned")
    _draw_arrow(ax, 0.68, 0.71, 0.74, 0.71, "Features")
    _draw_arrow(ax, 0.58, 0.62, 0.36, 0.33, "Save CSV")
    _draw_arrow(ax, 0.60, 0.62, 0.63, 0.33, "Batch Load")
    _draw_arrow(ax, 0.85, 0.62, 0.87, 0.33, "Insights")
    _draw_arrow(ax, 0.73, 0.24, 0.78, 0.24, "CRUD")

    fig.tight_layout()
    fig.savefig(DIAGRAMS_DIR / "data_flow_diagram.png", dpi=200)
    plt.close(fig)


def create_er_diagram() -> None:
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Entity-Relationship (ER) Diagram — MySQL Schema", fontsize=13, fontweight="bold", pad=12)

    _draw_box(ax, 0.05, 0.60, 0.25, 0.25, "STATIONS\n----------------\nPK: station_code\nstation_name", "#dbeafe", "#1d4ed8", 9)
    _draw_box(ax, 0.38, 0.60, 0.27, 0.28, "TRAINS\n----------------\nPK: train_no\nFK: origin_code\nFK: destination_code\nnumber_of_stops\ntotal_distance\ntotal_journey_duration_min", "#dcfce7", "#15803d", 8.5)
    _draw_box(ax, 0.71, 0.60, 0.25, 0.26, "PREDICTION_HISTORY\n----------------\nPK: prediction_id\ntrain_no (nullable)\nsegment_distance\npredicted_duration_min\nmodel_name, created_at", "#fef3c7", "#b45309", 8.5)

    _draw_box(ax, 0.12, 0.12, 0.34, 0.28, "TRAIN_SCHEDULES\n----------------\nPK: schedule_id\nFK: train_no -> TRAINS\nFK: station_code -> STATIONS\nsn, arrival_time, departure_time\ndistance, halt_duration_min\nfare_1a, fare_2a, fare_3a, fare_sl", "#ede9fe", "#6d28d9", 8.5)
    _draw_box(ax, 0.54, 0.12, 0.35, 0.28, "TRAIN_ROUTES\n----------------\nPK: route_id\nFK: train_no -> TRAINS\nFK: from_station_code -> STATIONS\nFK: to_station_code -> STATIONS\nstop_sequence, segment_distance\nsegment_duration_min, segment_speed", "#fee2e2", "#b91c1c", 8.5)

    _draw_arrow(ax, 0.30, 0.73, 0.38, 0.73, "1 : N")
    _draw_arrow(ax, 0.18, 0.60, 0.25, 0.40, "1 : N")
    _draw_arrow(ax, 0.48, 0.60, 0.35, 0.40, "1 : N")
    _draw_arrow(ax, 0.55, 0.60, 0.68, 0.40, "1 : N")
    _draw_arrow(ax, 0.25, 0.60, 0.60, 0.40, "1 : N")

    fig.tight_layout()
    fig.savefig(DIAGRAMS_DIR / "er_diagram.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    create_system_architecture()
    create_data_flow_diagram()
    create_er_diagram()
    print("Generated MCA diagrams successfully.")
