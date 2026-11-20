
import pandas as pd

from sqlalchemy import text

from src.database import get_database_engine
from src.logger import get_logger


logger = get_logger()


WEATHER_COLUMNS = [
    "city",
    "latitude",
    "longitude",
    "observation_time",
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "weather_code",
    "wind_speed_10m"
]


def validate_dataframe_columns(dataframe, required_columns):
    """
    Check whether a DataFrame contains all required columns.
    """

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )


def prepare_records(dataframe):
    """
    Convert a DataFrame into database-friendly records.
    Replace pandas missing values with Python None.
    """

    cleaned_df = dataframe.astype(object).where(
        pd.notna(dataframe),
        None
    )

    records = cleaned_df.to_dict(orient="records")

    # Invalid timestamps in rejected records must be stored as NULL,
    # because PostgreSQL cannot store arbitrary invalid date strings.
    for record in records:

        observation_time = record.get("observation_time")

        if observation_time is not None:

            parsed_time = pd.to_datetime(
                observation_time,
                errors="coerce"
            )

            if pd.isna(parsed_time):
                record["observation_time"] = None
            elif isinstance(parsed_time, pd.Timestamp):
                record["observation_time"] = parsed_time.to_pydatetime()

    return records



def load_weather_data(valid_df):
    """
    Load validated weather records into PostgreSQL.

    Duplicate city and observation-time combinations are skipped.
    Records are inserted individually to support reliable
    PostgreSQL RETURNING results.
    """

    if valid_df.empty:
        logger.warning("No valid records available to load.")
        print("No valid records available to load.")
        return 0

    validate_dataframe_columns(valid_df, WEATHER_COLUMNS)

    records = prepare_records(valid_df)

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
        RETURNING id
    """)

    engine = None

    try:
        logger.info("Starting PostgreSQL database loading")
        logger.info("Records received for loading: %d", len(records))

        engine = get_database_engine()

        inserted_count = 0

        with engine.begin() as connection:

            for record in records:

                result = connection.execute(
                    insert_query,
                    record
                )

                inserted_id = result.scalar_one_or_none()

                if inserted_id is not None:
                    inserted_count += 1

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
        if engine is not None:
            engine.dispose()


def load_rejected_records(rejected_df):
    """
    Save rejected weather records and their validation reasons
    into the rejected_weather_records PostgreSQL table.

    Rejected records are append-only so that historical
    validation failures remain available for monitoring.
    """

    if rejected_df.empty:
        logger.info("No rejected records available to load.")
        print("No rejected records to save.")
        return 0

    required_columns = WEATHER_COLUMNS + ["rejection_reason"]

    validate_dataframe_columns(rejected_df, required_columns)

    records = prepare_records(rejected_df)

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

    engine = None

    try:
        logger.info("Saving rejected weather records")
        logger.info("Rejected records received: %d", len(records))

        engine = get_database_engine()

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
        if engine is not None:
            engine.dispose()
