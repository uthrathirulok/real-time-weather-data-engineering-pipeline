
import pandas as pd
import pytest

from src.transform import transform_weather_data


def create_valid_record(**overrides):
    record = {
        "city": "Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "observation_time": "2026-11-18T10:00",
        "temperature_2m": 28.5,
        "relative_humidity_2m": 65,
        "apparent_temperature": 30.0,
        "precipitation": 0.0,
        "weather_code": 1,
        "wind_speed_10m": 12.5
    }

    record.update(overrides)
    return record


def test_valid_record_is_accepted():
    valid_df, rejected_df = transform_weather_data(
        [create_valid_record()]
    )

    assert len(valid_df) == 1
    assert rejected_df.empty


def test_invalid_temperature_is_rejected():
    valid_df, rejected_df = transform_weather_data(
        [create_valid_record(temperature_2m=100)]
    )

    assert valid_df.empty
    assert len(rejected_df) == 1
    assert "temperature_2m outside range" in rejected_df.iloc[0]["rejection_reason"]


def test_missing_temperature_is_rejected():
    valid_df, rejected_df = transform_weather_data(
        [create_valid_record(temperature_2m=None)]
    )

    assert valid_df.empty
    assert len(rejected_df) == 1
    assert "Missing or invalid value: temperature_2m" in rejected_df.iloc[0]["rejection_reason"]


def test_missing_required_column_raises_error():
    record = create_valid_record()
    del record["temperature_2m"]

    with pytest.raises(ValueError, match="Missing required columns"):
        transform_weather_data([record])


def test_missing_city_is_rejected():
    valid_df, rejected_df = transform_weather_data(
        [create_valid_record(city="")]
    )

    assert valid_df.empty
    assert len(rejected_df) == 1
    assert "Missing or invalid value: city" in rejected_df.iloc[0]["rejection_reason"]


def test_missing_observation_time_is_rejected():
    valid_df, rejected_df = transform_weather_data(
        [create_valid_record(observation_time=None)]
    )

    assert valid_df.empty
    assert len(rejected_df) == 1
    assert "Missing or invalid value: observation_time" in rejected_df.iloc[0]["rejection_reason"]


def test_invalid_observation_time_is_rejected():
    valid_df, rejected_df = transform_weather_data(
        [create_valid_record(observation_time="not-a-date")]
    )

    assert valid_df.empty
    assert len(rejected_df) == 1


def test_duplicate_records_are_removed():
    record = create_valid_record()

    valid_df, rejected_df = transform_weather_data(
        [record, record]
    )

    assert len(valid_df) == 1
    assert rejected_df.empty


def test_last_duplicate_record_is_kept():
    first_record = create_valid_record(temperature_2m=25)
    last_record = create_valid_record(temperature_2m=30)

    valid_df, rejected_df = transform_weather_data(
        [first_record, last_record]
    )

    assert len(valid_df) == 1
    assert valid_df.iloc[0]["temperature_2m"] == 30
    assert rejected_df.empty


@pytest.mark.parametrize(
    "column,value",
    [
        ("latitude", 91),
        ("longitude", 181),
        ("temperature_2m", 61),
        ("relative_humidity_2m", 101),
        ("apparent_temperature", 71),
        ("precipitation", 1001),
        ("weather_code", 100),
        ("wind_speed_10m", 401)
    ]
)
def test_values_outside_maximum_range_are_rejected(column, value):
    valid_df, rejected_df = transform_weather_data(
        [create_valid_record(**{column: value})]
    )

    assert valid_df.empty
    assert len(rejected_df) == 1


@pytest.mark.parametrize(
    "column,value",
    [
        ("latitude", -90),
        ("longitude", -180),
        ("temperature_2m", -80),
        ("relative_humidity_2m", 0),
        ("apparent_temperature", -100),
        ("precipitation", 0),
        ("weather_code", 0),
        ("wind_speed_10m", 0)
    ]
)
def test_minimum_boundary_values_are_accepted(column, value):
    valid_df, rejected_df = transform_weather_data(
        [create_valid_record(**{column: value})]
    )

    assert len(valid_df) == 1
    assert rejected_df.empty


@pytest.mark.parametrize(
    "column,value",
    [
        ("latitude", 90),
        ("longitude", 180),
        ("temperature_2m", 60),
        ("relative_humidity_2m", 100),
        ("apparent_temperature", 70),
        ("precipitation", 1000),
        ("weather_code", 99),
        ("wind_speed_10m", 400)
    ]
)
def test_maximum_boundary_values_are_accepted(column, value):
    valid_df, rejected_df = transform_weather_data(
        [create_valid_record(**{column: value})]
    )

    assert len(valid_df) == 1
    assert rejected_df.empty


def test_infinite_numeric_value_is_rejected():
    valid_df, rejected_df = transform_weather_data(
        [create_valid_record(temperature_2m=float("inf"))]
    )

    assert valid_df.empty
    assert len(rejected_df) == 1
    assert "non-finite" in rejected_df.iloc[0]["rejection_reason"]


def test_multiple_validation_errors_are_recorded():
    valid_df, rejected_df = transform_weather_data(
        [
            create_valid_record(
                temperature_2m=100,
                relative_humidity_2m=None
            )
        ]
    )

    assert valid_df.empty
    assert len(rejected_df) == 1

    reason = rejected_df.iloc[0]["rejection_reason"]

    assert "temperature_2m outside range" in reason
    assert "Missing or invalid value: relative_humidity_2m" in reason


def test_empty_input_returns_empty_dataframes():
    valid_df, rejected_df = transform_weather_data([])

    assert valid_df.empty
    assert rejected_df.empty
