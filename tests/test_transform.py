
from src.transform import transform_weather_data


def create_weather_record(
    city="Chennai",
    temperature=28.5,
    humidity=70,
    apparent_temperature=30.0,
    precipitation=0.0,
    weather_code=1,
    wind_speed=12.0
):
    """Create a sample weather record for testing."""

    return {
        "city": city,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "observation_time": "2026-11-14T22:00",
        "temperature_2m": temperature,
        "relative_humidity_2m": humidity,
        "apparent_temperature": apparent_temperature,
        "precipitation": precipitation,
        "weather_code": weather_code,
        "wind_speed_10m": wind_speed
    }


def test_valid_weather_record_is_accepted():

    records = [create_weather_record()]

    valid_df, rejected_df = transform_weather_data(records)

    assert len(valid_df) == 1
    assert len(rejected_df) == 0


def test_invalid_temperature_is_rejected():

    records = [
        create_weather_record(temperature=100)
    ]

    valid_df, rejected_df = transform_weather_data(records)

    assert len(valid_df) == 0
    assert len(rejected_df) == 1

    assert "temperature_2m outside range" in (
        rejected_df.iloc[0]["rejection_reason"]
    )


def test_missing_weather_measurement_is_rejected():

    records = [
        create_weather_record(temperature=None)
    ]

    valid_df, rejected_df = transform_weather_data(records)

    assert len(valid_df) == 0
    assert len(rejected_df) == 1

    assert "Missing or invalid value: temperature_2m" in (
        rejected_df.iloc[0]["rejection_reason"]
    )


def test_duplicate_weather_records_are_removed():

    record = create_weather_record()

    records = [record, record.copy()]

    valid_df, rejected_df = transform_weather_data(records)

    assert len(valid_df) == 1
    assert len(rejected_df) == 0
