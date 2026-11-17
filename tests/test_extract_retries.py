import requests
from unittest.mock import Mock, patch

from src.extract import fetch_weather


def test_weather_api_retries_and_succeeds():

    # Simulate a successful weather API response
    mock_response = Mock()

    mock_response.json.return_value = {
        "current": {
            "time": "2026-11-14T22:00",
            "temperature_2m": 28.5,
            "relative_humidity_2m": 70,
            "apparent_temperature": 30.0,
            "precipitation": 0.0,
            "weather_code": 1,
            "wind_speed_10m": 12.0
        }
    }

    # Simulate two failures followed by success
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

            # Verify three API attempts
            assert mock_get.call_count == 3

            # Verify two retry waits
            assert mock_sleep.call_count == 2

            # Verify weather data was returned
            assert result is not None
            assert result["city"] == "Chennai"
            assert result["temperature_2m"] == 28.5

            print("\nRETRY TEST PASSED!")
            print("First attempt: Failed")
            print("Second attempt: Failed")
            print("Third attempt: Successful")
            print("Total API attempts: 3")
            print("Retry waits: 2")

def test_pipeline_continues_after_all_retries_fail():

    # Simulate a successful weather response for Bengaluru
    mock_response = Mock()

    mock_response.json.return_value = {
        "current": {
            "time": "2026-11-14T22:30",
            "temperature_2m": 27.5,
            "relative_humidity_2m": 65,
            "apparent_temperature": 29.0,
            "precipitation": 0.0,
            "weather_code": 1,
            "wind_speed_10m": 10.0
        }
    }

    # Chennai fails three times.
    # Bengaluru succeeds on its first attempt.
    simulated_results = [
        requests.exceptions.ConnectionError("Simulated API failure"),
        requests.exceptions.ConnectionError("Simulated API failure"),
        requests.exceptions.ConnectionError("Simulated API failure"),
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

    with patch(
        "src.extract.CITIES",
        test_cities
    ):

        with patch(
            "src.extract.requests.get",
            side_effect=simulated_results
        ) as mock_get:

            with patch("src.extract.time.sleep") as mock_sleep:

                from src.extract import extract_weather_data

                records = extract_weather_data()

                # Four API calls: three for Chennai, one for Bengaluru
                assert mock_get.call_count == 4

                # Two waits between Chennai's three attempts
                assert mock_sleep.call_count == 2

                # Chennai should be skipped
                # Bengaluru should be successfully extracted
                assert len(records) == 1
                assert records[0]["city"] == "Bengaluru"

                print("\nFAILURE HANDLING TEST PASSED!")
                print("Chennai: Failed after 3 attempts")
                print("Bengaluru: Successfully extracted")
                print("Pipeline continued after Chennai failed.")
