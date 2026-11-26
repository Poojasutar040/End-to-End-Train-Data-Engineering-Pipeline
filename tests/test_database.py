"""Unit tests for MySQL config and parameterized CRUD repository."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from database.repository import RailwayRepository
from utils.config import MySQLConfig


def test_mysql_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MYSQL_HOST", "localhost")
    monkeypatch.setenv("MYSQL_PORT", "3306")
    monkeypatch.setenv("MYSQL_USER", "mca_user")
    monkeypatch.setenv("MYSQL_PASSWORD", "strong_pass_123")
    monkeypatch.setenv("MYSQL_DATABASE", "smart_railway_db")

    cfg = MySQLConfig.from_env()
    assert cfg.host == "localhost"
    assert cfg.port == 3306
    assert cfg.is_password_configured() is True


def test_repository_station_crud_uses_parameterized_queries() -> None:
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    repo = RailwayRepository(
        MySQLConfig("localhost", 3306, "root", "real_secret", "smart_railway_db")
    )

    with patch("database.repository.get_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        repo.create_station("pune", "pune jn")
        sql, params = mock_cursor.execute.call_args[0]
        assert "%s" in sql
        assert params == ("PUNE", "PUNE JN")
        mock_conn.commit.assert_called_once()

    with pytest.raises(ValueError, match="Station code"):
        repo.create_station("INVALID CODE!", "NAME")
