
import math

import pandas as pd

from src.logger import get_logger


logger = get_logger()


def transform_weather_data(weather_records):
    """
    Convert extracted weather records into a DataFrame,
    validate metadata and weather measurements, and separate
    valid and rejected records.
    """

    if not weather_records:
        logger.warning("No weather records available for transformation.")
        print("No weather records available for transformation.")
        return pd.DataFrame(), pd.DataFrame()

    df = pd.DataFrame(weather_records)

    print("\n--- DATA TRANSFORMATION ---")
    print(f"Records received: {len(df)}")

    logger.info("Records received for transformation: %d", len(df))

    # Required fields used by the database and validation process
    required_columns = [
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

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        error_message = (
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

        logger.error(error_message)
        raise ValueError(error_message)

    # Convert numeric fields
    numeric_columns = [
        "latitude",
        "longitude",
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation",
        "weather_code",
        "wind_speed_10m"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Define acceptable value ranges
    validation_rules = {
        "latitude": (-90, 90),
        "longitude": (-180, 180),
        "temperature_2m": (-80, 60),
        "relative_humidity_2m": (0, 100),
        "apparent_temperature": (-100, 70),
        "precipitation": (0, 1000),
        "weather_code": (0, 99),
        "wind_speed_10m": (0, 400)
    }

    rejection_reasons = []

    # Validate each record
    for _, row in df.iterrows():

        reasons = []

        # Validate city
        city = row["city"]

        if pd.isna(city) or not isinstance(city, str) or not city.strip():
            reasons.append("Missing or invalid value: city")

        # Validate observation timestamp
        observation_time = row["observation_time"]

        if (
            pd.isna(observation_time)
            or not str(observation_time).strip()
            or pd.isna(pd.to_datetime(observation_time, errors="coerce"))
        ):
            reasons.append(
                "Missing or invalid value: observation_time"
            )

        # Validate numeric fields
        for column in numeric_columns:

            value = row[column]

            if pd.isna(value):
                reasons.append(
                    f"Missing or invalid value: {column}"
                )
                continue

            if not math.isfinite(float(value)):
                reasons.append(
                    f"Invalid non-finite value: {column}"
                )
                continue

            minimum, maximum = validation_rules[column]

            if value < minimum or value > maximum:
                reasons.append(
                    f"{column} outside range ({minimum} to {maximum})"
                )

        rejection_reasons.append("; ".join(reasons))

    df["rejection_reason"] = rejection_reasons

    # Identify records with valid city and timestamp keys
    valid_city_mask = (
        df["city"].apply(
            lambda value: isinstance(value, str) and bool(value.strip())
        )
    )

    valid_time_mask = df["observation_time"].apply(
        lambda value: (
            pd.notna(value)
            and bool(str(value).strip())
            and pd.notna(pd.to_datetime(value, errors="coerce"))
        )
    )

    valid_key_mask = valid_city_mask & valid_time_mask

    # Remove duplicate city/timestamp combinations.
    # Keep the most recent occurrence in the input data.
    duplicate_mask = pd.Series(False, index=df.index)

    duplicate_mask.loc[valid_key_mask] = (
        df.loc[valid_key_mask]
        .duplicated(
            subset=["city", "observation_time"],
            keep="last"
        )
    )

    duplicate_count = int(duplicate_mask.sum())

    df = df.loc[~duplicate_mask].copy()

    logger.info("Duplicate records removed: %d", duplicate_count)

    # Separate valid and rejected records
    rejected_mask = df["rejection_reason"] != ""

    valid_df = df.loc[~rejected_mask].copy()
    rejected_df = df.loc[rejected_mask].copy()

    # Calculate quality score after duplicate removal
    total_records = len(df)

    quality_score = (
        len(valid_df) / total_records * 100
        if total_records > 0
        else 0
    )

    print(f"Duplicate records removed: {duplicate_count}")
    print(f"Records after duplicate removal: {total_records}")
    print(f"Valid records: {len(valid_df)}")
    print(f"Rejected records: {len(rejected_df)}")
    print(f"Data quality score: {quality_score:.2f}%")

    # Log validation results
    logger.info("Valid records: %d", len(valid_df))
    logger.info("Rejected records: %d", len(rejected_df))
    logger.info("Data quality score: %.2f%%", quality_score)

    # Log individual rejection reasons
    if not rejected_df.empty:

        logger.warning("Rejected records and their reasons:")

        for _, row in rejected_df.iterrows():

            logger.warning(
                "City: %s | Observation: %s | Reason: %s",
                row["city"],
                row["observation_time"],
                row["rejection_reason"]
            )

    else:
        logger.info("No data quality issues detected.")

    print("\nMissing values:")
    print(df[numeric_columns].isnull().sum())

    return valid_df, rejected_df
