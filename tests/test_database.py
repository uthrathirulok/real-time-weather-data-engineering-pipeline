
from unittest.mock import MagicMock, patch

import pytest

from src import database


def set_valid_database_settings(monkeypatch):
    """Set valid database configuration for testing."""

    monkeypatch.setattr(database, "DB_HOST", "localhost")
    monkeypatch.setattr(database, "DB_PORT", "5432")
    monkeypatch.setattr(database, "DB_NAME", "weather_pipeline")
    monkeypatch.setattr(database, "DB_USER", "test_user")
    monkeypatch.setattr(database, "DB_PASSWORD", "test_password")


def test_missing_database_settings_raise_error(monkeypatch):
    set_valid_database_settings(monkeypatch)

    monkeypatch.setattr(database, "DB_PASSWORD", "")

    with pytest.raises(ValueError, match="DB_PASSWORD"):
        database.get_database_engine()


@pytest.mark.parametrize(
    "port",
    ["invalid", "5432.5", ""]
)
def test_invalid_database_port_raises_error(monkeypatch, port):
    set_valid_database_settings(monkeypatch)
    monkeypatch.setattr(database, "DB_PORT", port)

    with pytest.raises(ValueError, match="DB_PORT"):
        database.get_database_engine()


@pytest.mark.parametrize(
    "port",
    ["0", "65536"]
)
def test_database_port_out_of_range_raises_error(monkeypatch, port):
    set_valid_database_settings(monkeypatch)
    monkeypatch.setattr(database, "DB_PORT", port)

    with pytest.raises(ValueError, match="between 1 and 65535"):
        database.get_database_engine()


def test_database_engine_is_created_successfully(monkeypatch):
    set_valid_database_settings(monkeypatch)

    mock_engine = MagicMock()

    with patch(
        "src.database.create_engine",
        return_value=mock_engine
    ) as mock_create_engine:

        result = database.get_database_engine()

        assert result is mock_engine

        mock_create_engine.assert_called_once()

        engine_options = mock_create_engine.call_args.kwargs

        assert engine_options["pool_pre_ping"] is True


def test_database_connection_succeeds():

    mock_engine = MagicMock()

    with patch(
        "src.database.get_database_engine",
        return_value=mock_engine
    ):

        result = database.test_database_connection()

        assert result is True

        mock_engine.connect.assert_called_once()
        mock_engine.dispose.assert_called_once()


def test_database_connection_failure_returns_false():

    mock_engine = MagicMock()

    mock_engine.connect.side_effect = RuntimeError(
        "Simulated connection failure"
    )

    with patch(
        "src.database.get_database_engine",
        return_value=mock_engine
    ):

        result = database.test_database_connection()

        assert result is False
        mock_engine.dispose.assert_called_once()


def test_database_engine_creation_failure_returns_false():

    with patch(
        "src.database.get_database_engine",
        side_effect=RuntimeError("Engine creation failed")
    ):

        result = database.test_database_connection()

        assert result is False
