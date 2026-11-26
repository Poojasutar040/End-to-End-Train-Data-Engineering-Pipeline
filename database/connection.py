"""MySQL connection management and schema initialization helpers."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import mysql.connector
from mysql.connector import Error as MySQLError

from utils.config import PATHS, MySQLConfig
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseConnectionError(RuntimeError):
    """Raised when MySQL is unreachable or credentials are missing/invalid."""


@contextmanager
def get_connection(
    config: MySQLConfig | None = None,
    include_database: bool = True,
) -> Iterator[mysql.connector.MySQLConnection]:
    """Yield an open MySQL connection configured from environment variables."""
    cfg = config or MySQLConfig.from_env()
    if not cfg.is_password_configured():
        raise DatabaseConnectionError(
            "MYSQL_PASSWORD is not configured. Copy .env.example to .env and set your MySQL credentials."
        )

    conn_kwargs: dict[str, object] = {
        "host": cfg.host,
        "port": cfg.port,
        "user": cfg.user,
        "password": cfg.password,
        "connection_timeout": 5,
    }
    if include_database:
        conn_kwargs["database"] = cfg.database

    conn = None
    try:
        conn = mysql.connector.connect(**conn_kwargs)
        yield conn
    except MySQLError as exc:
        logger.error("MySQL connection failed: %s", exc)
        raise DatabaseConnectionError(
            f"Unable to connect to MySQL at {cfg.host}:{cfg.port} as '{cfg.user}'. "
            f"Ensure MySQL Server is running and .env credentials are valid. Details: {exc}"
        ) from exc
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


def test_connection(config: MySQLConfig | None = None) -> tuple[bool, str]:
    """Check whether MySQL is reachable and return (ok, status_message)."""
    cfg = config or MySQLConfig.from_env()
    try:
        with get_connection(cfg, include_database=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version_row = cursor.fetchone()
            cursor.close()
            version = version_row[0] if version_row else "unknown"
            return True, f"Connected to MySQL {version} on {cfg.host}:{cfg.port}."
    except DatabaseConnectionError as exc:
        return False, str(exc)


def initialize_database(config: MySQLConfig | None = None) -> None:
    """Create the target database and tables defined in database/schema.sql."""
    cfg = config or MySQLConfig.from_env()
    schema_path = PATHS.schema_sql_path
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema SQL file not found: {schema_path}")

    sql_text = schema_path.read_text(encoding="utf-8")
    statements = [stmt.strip() for stmt in sql_text.split(";") if stmt.strip()]

    with get_connection(cfg, include_database=False) as conn:
        cursor = conn.cursor()
        for stmt in statements:
            # Replace default DB name if user configured a custom MYSQL_DATABASE
            adjusted = stmt.replace("smart_railway_db", cfg.database)
            cursor.execute(adjusted)
        conn.commit()
        cursor.close()
    logger.info("Initialized MySQL database '%s' from %s.", cfg.database, schema_path)
