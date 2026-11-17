
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


def fetch_weather(city_name, city_config):
    """
    Fetch current weather data for one city.
    Retry automatically if the API request fails.
    """

    params = {
        "latitude": city_config["latitude"],
        "longitude": city_config["longitude"],
        "current": ",".join(WEATHER_FIELDS),
        "timezone": "auto"
    }

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

            if "current" not in weather_data:
                raise ValueError(
                    "Current weather data is missing from API response."
                )

            current_weather = weather_data["current"]

            record = {
                "city": city_name,
                "latitude": city_config["latitude"],
                "longitude": city_config["longitude"],
                "observation_time": current_weather.get("time")
            }

            for field in WEATHER_FIELDS:
                record[field] = current_weather.get(field)

            logger.info(
                "Successfully fetched weather data for %s",
                city_name
            )

            return record

        except (requests.exceptions.RequestException, ValueError, KeyError) as error:

            logger.warning(
                "Attempt %d/%d failed for %s: %s",
                attempt,
                MAX_RETRIES,
                city_name,
                error
            )

            if attempt < MAX_RETRIES:

                logger.info(
                    "Retrying %s in %d seconds...",
                    city_name,
                    RETRY_DELAY_SECONDS
                )

                print(
                    f"Retrying {city_name} in "
                    f"{RETRY_DELAY_SECONDS} seconds..."
                )

                time.sleep(RETRY_DELAY_SECONDS)

            else:

                logger.error(
                    "All %d attempts failed for %s.",
                    MAX_RETRIES,
                    city_name
                )

                print(
                    f"Failed to fetch weather data for {city_name} "
                    f"after {MAX_RETRIES} attempts."
                )

    return None


def extract_weather_data():
    """
    Fetch weather data for all configured cities.
    """

    weather_records = []

    for city_name, city_config in CITIES.items():

        print(f"Fetching weather data for {city_name}...")

        logger.info("Starting weather extraction for %s", city_name)

        record = fetch_weather(city_name, city_config)

        if record is not None:

            weather_records.append(record)

            print(f"Successfully fetched data for {city_name}.")

        else:

            logger.warning(
                "Weather extraction returned no record for %s",
                city_name
            )

    print(f"\nTotal successful records: {len(weather_records)}")

    logger.info(
        "Total successful weather records: %d",
        len(weather_records)
    )

    return weather_records
