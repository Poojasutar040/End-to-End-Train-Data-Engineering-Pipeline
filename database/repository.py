"""Parameterized CRUD repository for MySQL railway tables."""

from __future__ import annotations

from typing import Any

from database.connection import get_connection
from utils.config import MySQLConfig
from utils.validators import validate_non_negative_float, validate_positive_int, validate_station_code


class RailwayRepository:
    """Provides Create, Read, Update, Delete operations across railway tables."""

    def __init__(self, config: MySQLConfig | None = None) -> None:
        self.config = config or MySQLConfig.from_env()

    # -------------------- STATIONS CRUD --------------------
    def create_station(self, station_code: str, station_name: str) -> None:
        code = validate_station_code(station_code)
        name = station_name.strip().upper()
        if not name:
            raise ValueError("Station name cannot be empty.")
        sql = (
            "INSERT INTO stations (station_code, station_name) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE station_name = VALUES(station_name)"
        )
        with get_connection(self.config) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (code, name))
            conn.commit()
            cursor.close()

    def get_station(self, station_code: str) -> dict[str, Any] | None:
        code = validate_station_code(station_code)
        sql = "SELECT station_code, station_name FROM stations WHERE station_code = %s"
        with get_connection(self.config) as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (code,))
            row = cursor.fetchone()
            cursor.close()
            return row

    def update_station_name(self, station_code: str, new_name: str) -> int:
        code = validate_station_code(station_code)
        name = new_name.strip().upper()
        if not name:
            raise ValueError("Station name cannot be empty.")
        sql = "UPDATE stations SET station_name = %s WHERE station_code = %s"
        with get_connection(self.config) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (name, code))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected

    def delete_station(self, station_code: str) -> int:
        code = validate_station_code(station_code)
        sql = "DELETE FROM stations WHERE station_code = %s"
        with get_connection(self.config) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (code,))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected

    # -------------------- TRAINS CRUD --------------------
    def create_train(
        self,
        train_no: int,
        origin_code: str,
        destination_code: str,
        origin_departure: str,
        destination_arrival: str,
        number_of_stops: int,
        total_distance: int,
        total_journey_duration_minutes: float,
        avg_speed_kmph: float = 0.0,
        max_1a_fare: int = 0,
        max_sl_fare: int = 0,
    ) -> None:
        tno = validate_positive_int(train_no, "train_no")
        orig = validate_station_code(origin_code)
        dest = validate_station_code(destination_code)
        stops = validate_positive_int(number_of_stops, "number_of_stops")
        dist = int(validate_non_negative_float(total_distance, "total_distance"))
        dur = validate_non_negative_float(total_journey_duration_minutes, "total_journey_duration_minutes")

        sql = (
            "INSERT INTO trains (train_no, origin_code, destination_code, origin_departure, "
            "destination_arrival, number_of_stops, total_distance, total_journey_duration_minutes, "
            "avg_speed_kmph, max_1a_fare, max_sl_fare) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        with get_connection(self.config) as conn:
            cursor = conn.cursor()
            cursor.execute(
                sql,
                (
                    tno,
                    orig,
                    dest,
                    origin_departure,
                    destination_arrival,
                    stops,
                    dist,
                    dur,
                    float(avg_speed_kmph),
                    int(max_1a_fare),
                    int(max_sl_fare),
                ),
            )
            conn.commit()
            cursor.close()

    def get_train(self, train_no: int) -> dict[str, Any] | None:
        tno = validate_positive_int(train_no, "train_no")
        sql = (
            "SELECT t.*, s1.station_name AS origin_name, s2.station_name AS destination_name "
            "FROM trains t "
            "JOIN stations s1 ON t.origin_code = s1.station_code "
            "JOIN stations s2 ON t.destination_code = s2.station_code "
            "WHERE t.train_no = %s"
        )
        with get_connection(self.config) as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (tno,))
            row = cursor.fetchone()
            cursor.close()
            return row

    def update_train_summary(
        self,
        train_no: int,
        total_distance: int,
        total_journey_duration_minutes: float,
    ) -> int:
        tno = validate_positive_int(train_no, "train_no")
        dist = int(validate_non_negative_float(total_distance, "total_distance"))
        dur = validate_non_negative_float(total_journey_duration_minutes, "total_journey_duration_minutes")
        sql = (
            "UPDATE trains SET total_distance = %s, total_journey_duration_minutes = %s "
            "WHERE train_no = %s"
        )
        with get_connection(self.config) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (dist, dur, tno))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected

    def delete_train(self, train_no: int) -> int:
        tno = validate_positive_int(train_no, "train_no")
        sql = "DELETE FROM trains WHERE train_no = %s"
        with get_connection(self.config) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (tno,))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected

    # -------------------- SCHEDULES & ROUTES READ --------------------
    def get_train_schedule(self, train_no: int) -> list[dict[str, Any]]:
        tno = validate_positive_int(train_no, "train_no")
        sql = (
            "SELECT ts.sn, ts.train_no, ts.station_code, s.station_name, "
            "ts.arrival_time, ts.departure_time, ts.distance, ts.halt_duration_minutes, "
            "ts.fare_1a, ts.fare_2a, ts.fare_3a, ts.fare_sl "
            "FROM train_schedules ts "
            "JOIN stations s ON ts.station_code = s.station_code "
            "WHERE ts.train_no = %s ORDER BY ts.sn ASC"
        )
        with get_connection(self.config) as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (tno,))
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def get_train_routes(self, train_no: int) -> list[dict[str, Any]]:
        tno = validate_positive_int(train_no, "train_no")
        sql = (
            "SELECT route_id, train_no, from_station_code, to_station_code, "
            "stop_sequence, segment_distance, segment_duration_minutes, segment_speed_kmph "
            "FROM train_routes WHERE train_no = %s ORDER BY stop_sequence ASC"
        )
        with get_connection(self.config) as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (tno,))
            rows = cursor.fetchall()
            cursor.close()
            return rows

    # -------------------- PREDICTION HISTORY CRUD --------------------
    def log_prediction(
        self,
        segment_distance: float,
        total_train_distance: float,
        total_train_stops: int,
        stop_order_index: int,
        departure_hour: int,
        halt_duration_minutes: float,
        predicted_duration_minutes: float,
        model_name: str,
        train_no: int | None = None,
    ) -> int:
        sql = (
            "INSERT INTO prediction_history (train_no, segment_distance, total_train_distance, "
            "total_train_stops, stop_order_index, departure_hour, halt_duration_minutes, "
            "predicted_duration_minutes, model_name) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        with get_connection(self.config) as conn:
            cursor = conn.cursor()
            cursor.execute(
                sql,
                (
                    train_no,
                    float(segment_distance),
                    float(total_train_distance),
                    int(total_train_stops),
                    int(stop_order_index),
                    int(departure_hour),
                    float(halt_duration_minutes),
                    float(predicted_duration_minutes),
                    str(model_name),
                ),
            )
            conn.commit()
            inserted_id = int(cursor.lastrowid)
            cursor.close()
            return inserted_id

    def get_prediction_history(self, limit: int = 50) -> list[dict[str, Any]]:
        safe_limit = validate_positive_int(limit, "limit")
        sql = (
            "SELECT prediction_id, train_no, segment_distance, total_train_distance, "
            "total_train_stops, stop_order_index, departure_hour, halt_duration_minutes, "
            "predicted_duration_minutes, model_name, created_at "
            "FROM prediction_history ORDER BY created_at DESC LIMIT %s"
        )
        with get_connection(self.config) as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (safe_limit,))
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def delete_prediction(self, prediction_id: int) -> int:
        pid = validate_positive_int(prediction_id, "prediction_id")
        sql = "DELETE FROM prediction_history WHERE prediction_id = %s"
        with get_connection(self.config) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (pid,))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected
