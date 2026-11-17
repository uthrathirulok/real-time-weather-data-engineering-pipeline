
from sqlalchemy import text

from src.database import get_database_engine
from src.logger import get_logger


logger = get_logger()


def load_weather_data(valid_df):
    """
    Load validated weather records into PostgreSQL.
    """

    if valid_df.empty:
        logger.warning("No valid records available to load.")
        print("No valid records available to load.")
        return 0

    engine = get_database_engine()

    insert_query = text("""
        INSERT INTO weather_records (
            city,
            latitude,
            longitude,
            observation_time,
            temperature_2m,
            relative_humidity_2m,
            apparent_temperature,
            precipitation,
            weather_code,
            wind_speed_10m
        )
        VALUES (
            :city,
            :latitude,
            :longitude,
            :observation_time,
            :temperature_2m,
            :relative_humidity_2m,
            :apparent_temperature,
            :precipitation,
            :weather_code,
            :wind_speed_10m
        )
        ON CONFLICT (city, observation_time)
        DO NOTHING
    """)

    records = valid_df.to_dict(orient="records")

    try:
        logger.info("Starting PostgreSQL database loading")
        logger.info("Records received for loading: %d", len(records))

        with engine.begin() as connection:
            result = connection.execute(insert_query, records)

        inserted_count = result.rowcount
        skipped_count = len(records) - inserted_count

        print("\n--- DATABASE LOAD RESULTS ---")
        print(f"Records received: {len(records)}")
        print(f"Records inserted: {inserted_count}")
        print(f"Records skipped: {skipped_count}")

        logger.info("Records inserted: %d", inserted_count)
        logger.info("Records skipped: %d", skipped_count)
        logger.info("Database loading completed successfully")

        return inserted_count

    except Exception:
        logger.exception("Database loading failed")
        raise

    finally:
        engine.dispose()


def load_rejected_records(rejected_df):
    """
    Save rejected weather records and their validation reasons
    into the rejected_weather_records PostgreSQL table.
    """

    if rejected_df.empty:
        logger.info("No rejected records available to load.")
        print("No rejected records to save.")
        return 0

    engine = get_database_engine()

    insert_query = text("""
        INSERT INTO rejected_weather_records (
            city,
            latitude,
            longitude,
            observation_time,
            temperature_2m,
            relative_humidity_2m,
            apparent_temperature,
            precipitation,
            weather_code,
            wind_speed_10m,
            rejection_reason
        )
        VALUES (
            :city,
            :latitude,
            :longitude,
            :observation_time,
            :temperature_2m,
            :relative_humidity_2m,
            :apparent_temperature,
            :precipitation,
            :weather_code,
            :wind_speed_10m,
            :rejection_reason
        )
    """)

    records = rejected_df.to_dict(orient="records")

    try:
        logger.info("Saving rejected weather records")
        logger.info("Rejected records received: %d", len(records))

        with engine.begin() as connection:
            connection.execute(insert_query, records)

        rejected_count = len(records)

        print("\n--- REJECTED RECORDS ---")
        print(f"Rejected records saved: {rejected_count}")

        logger.info(
            "Rejected records saved successfully: %d",
            rejected_count
        )

        return rejected_count

    except Exception:
        logger.exception("Failed to save rejected weather records")
        raise

    finally:
        engine.dispose()
