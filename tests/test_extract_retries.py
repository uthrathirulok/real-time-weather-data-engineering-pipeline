import requests
import pytest
from unittest.mock import Mock, patch

from src.extract import (
    fetch_weather,
    extract_weather_data
)


def create_weather_response(city_time="2026-11-14T22:00"):
    """Create a simulated successful weather API response."""

    mock_response = Mock()

    mock_response.json.return_value = {
        "current": {
            "time": city_time,
            "temperature_2m": 28.5,
            "relative_humidity_2m": 70,
            "apparent_temperature": 30.0,
            "precipitation": 0.0,
            "weather_code": 1,
            "wind_speed_10m": 12.0
        }
    }

    return mock_response


def test_weather_api_retries_and_succeeds():

    mock_response = create_weather_response()

    simulated_failures = [
        requests.exceptions.ConnectionError(
            "Simulated temporary API failure"
        ),
        requests.exceptions.ConnectionError(
            "Simulated temporary API failure"
        ),
        mock_response
    ]

    with patch(
        "src.extract.requests.get",
        side_effect=simulated_failures
    ) as mock_get:

        with patch("src.extract.time.sleep") as mock_sleep:

            city_config = {
                "latitude": 13.0827,
                "longitude": 80.2707
            }

            result = fetch_weather("Chennai", city_config)

            assert mock_get.call_count == 3
            assert mock_sleep.call_count == 2

            assert result is not None
            assert result["city"] == "Chennai"
            assert result["temperature_2m"] == 28.5

            print("\nRETRY TEST PASSED!")


def test_pipeline_continues_after_all_retries_fail():

    mock_response = create_weather_response(
        "2026-11-14T22:30"
    )

    simulated_results = [
        requests.exceptions.ConnectionError(
            "Simulated API failure"
        ),
        requests.exceptions.ConnectionError(
            "Simulated API failure"
        ),
        requests.exceptions.ConnectionError(
            "Simulated API failure"
        ),
        mock_response
    ]

    test_cities = {
        "Chennai": {
            "latitude": 13.0827,
            "longitude": 80.2707
        },
        "Bengaluru": {
            "latitude": 12.9716,
            "longitude": 77.5946
        }
    }

    with patch("src.extract.CITIES", test_cities):

        with patch(
            "src.extract.requests.get",
            side_effect=simulated_results
        ) as mock_get:

            with patch("src.extract.time.sleep") as mock_sleep:

                result = extract_weather_data()

                assert mock_get.call_count == 4
                assert mock_sleep.call_count == 2

                assert len(result["records"]) == 1
                assert result["records"][0]["city"] == "Bengaluru"

                assert result["successful_cities"] == ["Bengaluru"]

                assert "Chennai" in result["failed_cities"]

                print("\nFAILURE HANDLING TEST PASSED!")


def test_all_cities_fail():

    test_cities = {
        "Chennai": {
            "latitude": 13.0827,
            "longitude": 80.2707
        },
        "Bengaluru": {
            "latitude": 12.9716,
            "longitude": 77.5946
        }
    }

    with patch("src.extract.CITIES", test_cities):

        with patch(
            "src.extract.requests.get",
            side_effect=requests.exceptions.ConnectionError(
                "API unavailable"
            )
        ):

            with patch("src.extract.time.sleep"):

                result = extract_weather_data()

                assert result["records"] == []
                assert result["successful_cities"] == []
                assert len(result["failed_cities"]) == 2


def test_malformed_api_response_is_not_retried():

    mock_response = Mock()
    mock_response.json.return_value = {
        "current": "invalid structure"
    }

    city_config = {
        "latitude": 13.0827,
        "longitude": 80.2707
    }

    with patch(
        "src.extract.requests.get",
        return_value=mock_response
    ) as mock_get:

        with patch("src.extract.time.sleep") as mock_sleep:

            result = fetch_weather("Chennai", city_config)

            assert result is None
            assert mock_get.call_count == 1
            assert mock_sleep.call_count == 0


def test_http_400_is_not_retried():

    mock_response = Mock()

    mock_response.status_code = 400

    http_error = requests.exceptions.HTTPError(
        "Bad request",
        response=mock_response
    )

    with patch(
        "src.extract.requests.get",
        side_effect=http_error
    ) as mock_get:

        with patch("src.extract.time.sleep") as mock_sleep:

            city_config = {
                "latitude": 13.0827,
                "longitude": 80.2707
            }

            result = fetch_weather("Chennai", city_config)

            assert result is None
            assert mock_get.call_count == 1
            assert mock_sleep.call_count == 0

@pytest.mark.parametrize("status_code", [429, 500, 503])
def test_retryable_http_errors_are_retried(status_code):

    mock_response = create_weather_response()

    http_error = requests.exceptions.HTTPError(
        f"HTTP {status_code}",
        response=Mock(status_code=status_code)
    )

    simulated_results = [
        http_error,
        mock_response
    ]

    city_config = {
        "latitude": 13.0827,
        "longitude": 80.2707
    }

    with patch(
        "src.extract.requests.get",
        side_effect=simulated_results
    ) as mock_get:

        with patch("src.extract.time.sleep") as mock_sleep:

            result = fetch_weather("Chennai", city_config)

            assert result is not None
            assert result["city"] == "Chennai"
            assert mock_get.call_count == 2
            assert mock_sleep.call_count == 1
