
import pandas as pd
import pytest

from unittest.mock import MagicMock, patch

from src.load import load_weather_data, load_rejected_records


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


def create_rejected_dataframe():
    """Create sample rejected weather data."""

    dataframe = create_valid_dataframe()

    dataframe["temperature_2m"] = 100
    dataframe["rejection_reason"] = (
        "temperature_2m outside range (-80 to 60)"
    )

    return dataframe



def create_mock_engine(inserted_ids=None):
    """Create a mocked SQLAlchemy engine."""

    mock_engine = MagicMock()

    mock_connection = (
        mock_engine.begin.return_value.__enter__.return_value
    )

    if inserted_ids is not None:
        mock_results = []

        for inserted_id in inserted_ids:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = inserted_id
            mock_results.append(mock_result)

        mock_connection.execute.side_effect = mock_results

    return mock_engine, mock_connection

def test_empty_dataframe_is_not_loaded():

    empty_df = pd.DataFrame()

    with patch("src.load.get_database_engine") as mock_engine:

        result = load_weather_data(empty_df)

        assert result == 0
        mock_engine.assert_not_called()



def test_valid_records_are_loaded_into_database():

    valid_df = create_valid_dataframe()

    mock_engine, mock_connection = create_mock_engine(
        inserted_ids=[1]
    )

    with patch(
        "src.load.get_database_engine",
        return_value=mock_engine
    ):

        result = load_weather_data(valid_df)

        assert result == 1
        mock_connection.execute.assert_called_once()
        mock_engine.dispose.assert_called_once()



def test_duplicate_records_are_counted_as_skipped():

    valid_df = pd.concat(
        [
            create_valid_dataframe(),
            create_valid_dataframe()
        ],
        ignore_index=True
    )

    # First record inserted (ID 1).
    # Second record skipped as a duplicate (None).
    mock_engine, mock_connection = create_mock_engine(
        inserted_ids=[1, None]
    )

    with patch(
        "src.load.get_database_engine",
        return_value=mock_engine
    ):

        result = load_weather_data(valid_df)

        assert result == 1
        assert mock_connection.execute.call_count == 2
        mock_engine.dispose.assert_called_once()


def test_database_loading_error_is_raised():

    valid_df = create_valid_dataframe()

    mock_engine = MagicMock()

    mock_connection = (
        mock_engine.begin.return_value.__enter__.return_value
    )

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


def test_missing_required_column_raises_error():

    valid_df = create_valid_dataframe()

    valid_df = valid_df.drop(columns=["temperature_2m"])

    with patch("src.load.get_database_engine") as mock_engine:

        with pytest.raises(
            ValueError,
            match="Missing required columns"
        ):
            load_weather_data(valid_df)

        mock_engine.assert_not_called()


def test_empty_rejected_dataframe_is_not_loaded():

    empty_df = pd.DataFrame()

    with patch("src.load.get_database_engine") as mock_engine:

        result = load_rejected_records(empty_df)

        assert result == 0
        mock_engine.assert_not_called()


def test_rejected_records_are_saved():

    rejected_df = create_rejected_dataframe()

    mock_engine, mock_connection = create_mock_engine()

    with patch(
        "src.load.get_database_engine",
        return_value=mock_engine
    ):

        result = load_rejected_records(rejected_df)

        assert result == 1
        mock_connection.execute.assert_called_once()
        mock_engine.dispose.assert_called_once()


def test_rejected_record_with_invalid_timestamp_is_saved_as_null():

    rejected_df = create_rejected_dataframe()

    rejected_df["observation_time"] = "invalid-timestamp"

    mock_engine, mock_connection = create_mock_engine()

    with patch(
        "src.load.get_database_engine",
        return_value=mock_engine
    ):

        result = load_rejected_records(rejected_df)

        assert result == 1

        inserted_records = (
            mock_connection.execute.call_args.args[1]
        )

        assert inserted_records[0]["observation_time"] is None

        mock_engine.dispose.assert_called_once()


def test_rejected_record_database_error_is_raised():

    rejected_df = create_rejected_dataframe()

    mock_engine = MagicMock()

    mock_connection = (
        mock_engine.begin.return_value.__enter__.return_value
    )

    mock_connection.execute.side_effect = RuntimeError(
        "Rejected record loading failed"
    )

    with patch(
        "src.load.get_database_engine",
        return_value=mock_engine
    ):

        with pytest.raises(
            RuntimeError,
            match="Rejected record loading failed"
        ):
            load_rejected_records(rejected_df)

        mock_engine.dispose.assert_called_once()
