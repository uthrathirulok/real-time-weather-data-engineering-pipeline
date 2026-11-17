
from datetime import datetime

from src.transform import transform_weather_data
from src.load import load_rejected_records


# Create one deliberately invalid weather record
test_weather_record = {
    "city": "TEST_CITY",
    "latitude": 13.0827,
    "longitude": 80.2707,
    "observation_time": datetime.now(),
    "temperature_2m": 100.0,  # Invalid: maximum allowed is 60
    "relative_humidity_2m": 65,
    "apparent_temperature": 35,
    "precipitation": 0,
    "weather_code": 1,
    "wind_speed_10m": 12
}


print("=" * 50)
print("DATA QUALITY FAILURE SIMULATION")
print("=" * 50)

# STEP 1: Validate the test record
valid_df, rejected_df = transform_weather_data(
    [test_weather_record]
)

print("\n--- VALIDATION RESULTS ---")
print(f"Valid records: {len(valid_df)}")
print(f"Rejected records: {len(rejected_df)}")

# STEP 2: Display rejection reason
if not rejected_df.empty:

    print("\n--- REJECTION REASON ---")
    print(rejected_df[["city", "rejection_reason"]].to_string(index=False))

    # STEP 3: Save rejected record to PostgreSQL
    print("\nSaving rejected test record to PostgreSQL...")

    saved_count = load_rejected_records(rejected_df)

    print(f"\nRejected records saved: {saved_count}")

    print("\nData quality failure simulation completed!")

else:
    print("\nERROR: The test record was not rejected.")
