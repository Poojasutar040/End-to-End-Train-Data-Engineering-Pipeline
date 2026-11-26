-- Smart Railway Analytics and Train Journey Prediction System
-- MySQL 8.0 Normalized Database Schema

CREATE DATABASE IF NOT EXISTS smart_railway_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE smart_railway_db;

CREATE TABLE IF NOT EXISTS stations (
    station_code VARCHAR(16) NOT NULL,
    station_name VARCHAR(120) NOT NULL,
    PRIMARY KEY (station_code),
    INDEX idx_station_name (station_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS trains (
    train_no INT NOT NULL,
    origin_code VARCHAR(16) NOT NULL,
    destination_code VARCHAR(16) NOT NULL,
    origin_departure TIME NOT NULL,
    destination_arrival TIME NOT NULL,
    number_of_stops INT NOT NULL,
    total_distance INT NOT NULL,
    total_journey_duration_minutes DECIMAL(10, 2) NOT NULL,
    avg_speed_kmph DECIMAL(8, 2) NOT NULL DEFAULT 0.00,
    max_1a_fare INT NOT NULL DEFAULT 0,
    max_sl_fare INT NOT NULL DEFAULT 0,
    PRIMARY KEY (train_no),
    CONSTRAINT fk_trains_origin FOREIGN KEY (origin_code) REFERENCES stations(station_code),
    CONSTRAINT fk_trains_destination FOREIGN KEY (destination_code) REFERENCES stations(station_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS train_schedules (
    schedule_id BIGINT NOT NULL AUTO_INCREMENT,
    train_no INT NOT NULL,
    sn INT NOT NULL,
    station_code VARCHAR(16) NOT NULL,
    route_number INT NOT NULL DEFAULT 1,
    arrival_time TIME NOT NULL,
    departure_time TIME NOT NULL,
    distance INT NOT NULL,
    halt_duration_minutes DECIMAL(8, 2) NOT NULL DEFAULT 0.00,
    fare_1a INT NOT NULL DEFAULT 0,
    fare_2a INT NOT NULL DEFAULT 0,
    fare_3a INT NOT NULL DEFAULT 0,
    fare_sl INT NOT NULL DEFAULT 0,
    PRIMARY KEY (schedule_id),
    UNIQUE KEY uq_train_sn (train_no, sn),
    INDEX idx_schedule_station (station_code),
    CONSTRAINT fk_schedules_train FOREIGN KEY (train_no) REFERENCES trains(train_no) ON DELETE CASCADE,
    CONSTRAINT fk_schedules_station FOREIGN KEY (station_code) REFERENCES stations(station_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS train_routes (
    route_id BIGINT NOT NULL AUTO_INCREMENT,
    train_no INT NOT NULL,
    from_station_code VARCHAR(16) NOT NULL,
    to_station_code VARCHAR(16) NOT NULL,
    stop_sequence INT NOT NULL,
    segment_distance INT NOT NULL,
    segment_duration_minutes DECIMAL(10, 2) NOT NULL,
    segment_speed_kmph DECIMAL(8, 2) NOT NULL DEFAULT 0.00,
    PRIMARY KEY (route_id),
    UNIQUE KEY uq_route_leg (train_no, stop_sequence),
    INDEX idx_route_pair (from_station_code, to_station_code),
    CONSTRAINT fk_routes_train FOREIGN KEY (train_no) REFERENCES trains(train_no) ON DELETE CASCADE,
    CONSTRAINT fk_routes_from FOREIGN KEY (from_station_code) REFERENCES stations(station_code),
    CONSTRAINT fk_routes_to FOREIGN KEY (to_station_code) REFERENCES stations(station_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS prediction_history (
    prediction_id BIGINT NOT NULL AUTO_INCREMENT,
    train_no INT NULL,
    segment_distance DECIMAL(10, 2) NOT NULL,
    total_train_distance DECIMAL(10, 2) NOT NULL,
    total_train_stops INT NOT NULL,
    stop_order_index INT NOT NULL,
    departure_hour TINYINT NOT NULL,
    halt_duration_minutes DECIMAL(8, 2) NOT NULL,
    predicted_duration_minutes DECIMAL(10, 2) NOT NULL,
    model_name VARCHAR(80) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (prediction_id),
    INDEX idx_prediction_created (created_at)
) ENGINE=InnoDB;
