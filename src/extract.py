
import time
import requests

from config.config import (
    API_URL,
    API_TIMEOUT_SECONDS,
    CITIES,
    WEATHER_FIELDS
)

from src.logger import get_logger


logger = get_logger()

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def _is_retryable_error(error):
    """
    Determine whether an API error should be retried.
    """

    if isinstance(error, requests.exceptions.HTTPError):
        status_code = error.response.status_code

        return status_code == 429 or status_code >= 500

    return isinstance(
        error,
        (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        )
    )


def _fetch_weather_with_status(city_name, city_config):
    """
    Fetch weather data and return both the record and failure reason.
    """

    params = {
        "latitude": city_config["latitude"],
        "longitude": city_config["longitude"],
        "current": ",".join(WEATHER_FIELDS),
        "timezone": "auto"
    }

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            logger.info(
                "Fetching weather for %s (attempt %d/%d)",
                city_name,
                attempt,
                MAX_RETRIES
            )

            response = requests.get(
                API_URL,
                params=params,
                timeout=API_TIMEOUT_SECONDS
            )

            response.raise_for_status()

            weather_data = response.json()

            if not isinstance(weather_data, dict):
                raise ValueError("API response must be a JSON object.")

            current_weather = weather_data.get("current")

            if not isinstance(current_weather, dict):
                raise ValueError(
                    "Current weather data is missing or malformed."
                )

            observation_time = current_weather.get("time")

            if not isinstance(observation_time, str) or not observation_time.strip():
                raise ValueError(
                    "Observation timestamp is missing or invalid."
                )

            record = {
                "city": city_name,
                "latitude": city_config["latitude"],
                "longitude": city_config["longitude"],
                "observation_time": observation_time
            }

            for field in WEATHER_FIELDS:
                record[field] = current_weather.get(field)

            logger.info(
                "Successfully fetched weather data for %s",
                city_name
            )

            return record, None

        except requests.exceptions.RequestException as error:

            last_error = error

            logger.warning(
                "Attempt %d/%d failed for %s: %s",
                attempt,
                MAX_RETRIES,
                city_name,
                error
            )

            if not _is_retryable_error(error):
                logger.error(
                    "Non-retryable API error for %s.",
                    city_name
                )
                break

        except (ValueError, KeyError, TypeError) as error:

            last_error = error

            logger.error(
                "Invalid API response for %s: %s",
                city_name,
                error
            )

            # Malformed responses are not retried.
            break

        if attempt < MAX_RETRIES:

            logger.info(
                "Retrying %s in %d seconds...",
                city_name,
                RETRY_DELAY_SECONDS
            )

            time.sleep(RETRY_DELAY_SECONDS)

    failure_reason = (
        str(last_error)
        if last_error is not None
        else "Weather extraction failed."
    )

    logger.error(
        "Weather extraction failed for %s: %s",
        city_name,
        failure_reason
    )

    return None, failure_reason


def fetch_weather(city_name, city_config):
    """
    Fetch weather data for one city.

    Returns a weather record on success or None on failure.
    """

    record, _ = _fetch_weather_with_status(
        city_name,
        city_config
    )

    return record


def extract_weather_data():
    """
    Fetch weather data for all configured cities.

    Returns records, successful cities, and failed cities.
    """

    weather_records = []
    successful_cities = []
    failed_cities = {}

    for city_name, city_config in CITIES.items():

        print(f"Fetching weather data for {city_name}...")

        logger.info(
            "Starting weather extraction for %s",
            city_name
        )

        record, failure_reason = _fetch_weather_with_status(
            city_name,
            city_config
        )

        if record is not None:

            weather_records.append(record)
            successful_cities.append(city_name)

            print(
                f"Successfully fetched data for {city_name}."
            )

        else:

            failed_cities[city_name] = failure_reason

            print(
                f"Failed to fetch weather data for {city_name}."
            )

    logger.info(
        "Extraction completed. Successful cities: %d, Failed cities: %d",
        len(successful_cities),
        len(failed_cities)
    )

    print("\nEXTRACTION SUMMARY")
    print(f"Successful cities: {len(successful_cities)}")
    print(f"Failed cities: {len(failed_cities)}")
    print(f"Total extracted records: {len(weather_records)}")

    return {
        "records": weather_records,
        "successful_cities": successful_cities,
        "failed_cities": failed_cities
    }
