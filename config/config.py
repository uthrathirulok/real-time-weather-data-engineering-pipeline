
# Open-Meteo API configuration

API_URL = "https://api.open-meteo.com/v1/forecast"

# Maximum time to wait for an API response
API_TIMEOUT_SECONDS = 15

# Cities included in the weather pipeline
CITIES = {
    "Chennai": {
        "latitude": 13.0827,
        "longitude": 80.2707
    },
    "Bengaluru": {
        "latitude": 12.9716,
        "longitude": 77.5946
    },
    "Mumbai": {
        "latitude": 19.0760,
        "longitude": 72.8777
    },
    "Delhi": {
        "latitude": 28.6139,
        "longitude": 77.2090
    },
    "Hyderabad": {
        "latitude": 17.3850,
        "longitude": 78.4867
    }
}

# Weather information we want to collect
WEATHER_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "weather_code",
    "wind_speed_10m"
]
