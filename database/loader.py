
"""Batch ETL loader to populate MySQL tables from processed railway DataFrames."""

from __future__ import annotations

from typing import Any

import pandas as pd

from database.connection import get_connection, initialize_database
from utils.config import MySQLConfig
from utils.logger import get_logger

logger = get_logger(__name__)

BATCH_SIZE = 5000


def _execute_batches(cursor: Any, sql: str, rows: list[tuple]) -> int:
    total = 0
    for idx in range(0, len(rows), BATCH_SIZE):
        chunk = rows[idx:idx + BATCH_SIZE]
        cursor.executemany(sql, chunk)
        total += len(chunk)
    return total


def _int(value: Any, default: int = 0) -> int:
    return default if pd.isna(value) else int(value)


def _float(value: Any, default: float = 0.0) -> float:
    return default if pd.isna(value) else float(value)


def _text(value: Any, default: str = "") -> str:
    return default if pd.isna(value) else str(value)


def load_all_to_mysql(
    features_df: pd.DataFrame,
    train_summary_df: pd.DataFrame,
    config: MySQLConfig | None = None,
) -> dict[str, int]:

    cfg = config or MySQLConfig.from_env()
    initialize_database(cfg)

    # 1. Stations
    stations_df = (
        features_df[["Station_Code", "Station_Name"]]
        .dropna(subset=["Station_Code", "Station_Name"])
        .drop_duplicates(subset=["Station_Code"])
        .sort_values("Station_Code")
    )

    station_rows = [
        (_text(r["Station_Code"]), _text(r["Station_Name"]))
        for r in stations_df.to_dict("records")
    ]

    # 2. Trains
    train_rows = [
        (
            _int(r["Train_No"]),
            _text(r["Origin_Code"]),
            _text(r["Destination_Code"]),
            _text(r["Origin_Departure"]),
            _text(r["Destination_Arrival"]),
            _int(r["Number_of_Stops"]),
            _int(r["Total_Distance"]),
            _float(r["Total_Journey_Duration_Minutes"]),
            _float(r["Avg_Speed_Kmph"]),
            _int(r["Max_1A_Fare"]),
            _int(r["Max_SL_Fare"]),
        )
        for r in train_summary_df.to_dict("records")
    ]

    # 3. Train schedules
    schedule_columns = [
        "Train_No", "SN", "Station_Code", "Route_Number",
        "Arrival_time", "Departure_Time", "Distance",
        "Halt_Duration_Minutes", "1A", "2A", "3A", "SL",
    ]

    schedule_df = features_df[schedule_columns].copy()
    fare_columns = ["1A", "2A", "3A", "SL"]
    schedule_df[fare_columns] = schedule_df[fare_columns].fillna(0)

    schedule_rows = [
        (
            _int(r["Train_No"]),
            _int(r["SN"]),
            _text(r["Station_Code"]),
            _int(r["Route_Number"], 1),
            _text(r["Arrival_time"], "00:00:00"),
            _text(r["Departure_Time"], "00:00:00"),
            _int(r["Distance"]),
            _float(r["Halt_Duration_Minutes"]),
            _int(r["1A"]),
            _int(r["2A"]),
            _int(r["3A"]),
            _int(r["SL"]),
        )
        for r in schedule_df.to_dict("records")
    ]

    # 4. Route segments
    legs_df = features_df.dropna(
        subset=[
            "Next_Station_Code",
            "Segment_Distance",
            "Journey_Duration_Minutes",
        ]
    )

    route_rows = [
        (
            _int(r["Train_No"]),
            _text(r["Station_Code"]),
            _text(r["Next_Station_Code"]),
            _int(r["SN"]),
            _int(r["Segment_Distance"]),
            _float(r["Journey_Duration_Minutes"]),
            _float(r["Segment_Speed_Kmph"]),
        )
        for r in legs_df[
            [
                "Train_No", "Station_Code", "Next_Station_Code",
                "SN", "Segment_Distance",
                "Journey_Duration_Minutes", "Segment_Speed_Kmph",
            ]
        ].to_dict("records")
    ]

    station_sql = """
        INSERT INTO stations (station_code, station_name)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE station_name = VALUES(station_name)
    """

    train_sql = """
        INSERT INTO trains (
            train_no, origin_code, destination_code,
            origin_departure, destination_arrival,
            number_of_stops, total_distance,
            total_journey_duration_minutes, avg_speed_kmph,
            max_1a_fare, max_sl_fare
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            origin_code = VALUES(origin_code),
            destination_code = VALUES(destination_code),
            origin_departure = VALUES(origin_departure),
            destination_arrival = VALUES(destination_arrival),
            number_of_stops = VALUES(number_of_stops),
            total_distance = VALUES(total_distance),
            total_journey_duration_minutes = VALUES(total_journey_duration_minutes),
            avg_speed_kmph = VALUES(avg_speed_kmph),
            max_1a_fare = VALUES(max_1a_fare),
            max_sl_fare = VALUES(max_sl_fare)
    """

    schedule_sql = """
        INSERT INTO train_schedules (
            train_no, sn, station_code, route_number,
            arrival_time, departure_time, distance,
            halt_duration_minutes, fare_1a, fare_2a, fare_3a, fare_sl
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            station_code = VALUES(station_code),
            route_number = VALUES(route_number),
            arrival_time = VALUES(arrival_time),
            departure_time = VALUES(departure_time),
            distance = VALUES(distance),
            halt_duration_minutes = VALUES(halt_duration_minutes),
            fare_1a = VALUES(fare_1a),
            fare_2a = VALUES(fare_2a),
            fare_3a = VALUES(fare_3a),
            fare_sl = VALUES(fare_sl)
    """

    route_sql = """
        INSERT INTO train_routes (
            train_no, from_station_code, to_station_code,
            stop_sequence, segment_distance,
            segment_duration_minutes, segment_speed_kmph
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            from_station_code = VALUES(from_station_code),
            to_station_code = VALUES(to_station_code),
            segment_distance = VALUES(segment_distance),
            segment_duration_minutes = VALUES(segment_duration_minutes),
            segment_speed_kmph = VALUES(segment_speed_kmph)
    """

    with get_connection(cfg, include_database=True) as conn:
        cursor = conn.cursor()
        try:
            counts = {
                "stations": _execute_batches(cursor, station_sql, station_rows),
                "trains": _execute_batches(cursor, train_sql, train_rows),
                "train_schedules": _execute_batches(cursor, schedule_sql, schedule_rows),
                "train_routes": _execute_batches(cursor, route_sql, route_rows),
            }
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    logger.info("Loaded records into MySQL: %s", counts)
    return counts
