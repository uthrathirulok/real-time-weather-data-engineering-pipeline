
import pandas as pd
import pytest

from unittest.mock import MagicMock, patch

from src.load import load_weather_data


def create_valid_dataframe():
    """Create sample valid weather data."""

    return pd.DataFrame([
        {
            "city": "Chennai",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "observation_time": "2026-11-14T22:00",
            "temperature_2m": 28.5,
            "relative_humidity_2m": 70,
            "apparent_temperature": 30.0,
            "precipitation": 0.0,
            "weather_code": 1,
            "wind_speed_10m": 12.0
        }
    ])


def test_empty_dataframe_is_not_loaded():

    empty_df = pd.DataFrame()

    with patch("src.load.get_database_engine") as mock_engine:

        result = load_weather_data(empty_df)

        assert result == 0
        mock_engine.assert_not_called()


def test_valid_records_are_loaded_into_database():

    valid_df = create_valid_dataframe()

    mock_engine = MagicMock()
    mock_connection = mock_engine.begin.return_value.__enter__.return_value

    mock_result = MagicMock()
    mock_result.rowcount = 1

    mock_connection.execute.return_value = mock_result

    with patch(
        "src.load.get_database_engine",
        return_value=mock_engine
    ):

        result = load_weather_data(valid_df)

        assert result == 1
        mock_connection.execute.assert_called_once()
        mock_engine.dispose.assert_called_once()


def test_database_loading_error_is_raised():

    valid_df = create_valid_dataframe()

    mock_engine = MagicMock()
    mock_connection = mock_engine.begin.return_value.__enter__.return_value

    mock_connection.execute.side_effect = RuntimeError(
        "Simulated database failure"
    )

    with patch(
        "src.load.get_database_engine",
        return_value=mock_engine
    ):

        with pytest.raises(
            RuntimeError,
            match="Simulated database failure"
        ):
            load_weather_data(valid_df)

        mock_engine.dispose.assert_called_once()
