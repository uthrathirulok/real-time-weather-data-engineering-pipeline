
import pandas as pd

from src.logger import get_logger


logger = get_logger()


def transform_weather_data(weather_records):
    """
    Convert extracted weather records into a DataFrame,
    validate weather measurements, and identify rejection reasons.
    """

    if not weather_records:
        logger.warning("No weather records available for transformation.")
        print("No weather records available for transformation.")
        return pd.DataFrame(), pd.DataFrame()

    # Convert records into a Pandas DataFrame
    df = pd.DataFrame(weather_records)

    print("\n--- DATA TRANSFORMATION ---")
    print(f"Records received: {len(df)}")

    logger.info("Records received for transformation: %d", len(df))

    # Remove duplicate records
    original_count = len(df)

    df = df.drop_duplicates(
        subset=["city", "observation_time"],
        keep="last"
    ).copy()

    duplicate_count = original_count - len(df)

    logger.info("Duplicate records removed: %d", duplicate_count)

    # Convert weather measurements into numeric values
    numeric_columns = [
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation",
        "weather_code",
        "wind_speed_10m"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # Define validation rules
    validation_rules = {
        "temperature_2m": (-80, 60),
        "relative_humidity_2m": (0, 100),
        "apparent_temperature": (-100, 70),
        "precipitation": (0, 1000),
        "weather_code": (0, 99),
        "wind_speed_10m": (0, 400)
    }

    # Store rejection reasons for each record
    rejection_reasons = []

    for index, row in df.iterrows():

        reasons = []

        # Check for missing values
        for column in numeric_columns:
            if pd.isna(row[column]):
                reasons.append(f"Missing or invalid value: {column}")

        # Check acceptable value ranges
        for column, (minimum, maximum) in validation_rules.items():

            value = row[column]

            if pd.notna(value):
                if value < minimum or value > maximum:
                    reasons.append(
                        f"{column} outside range ({minimum} to {maximum})"
                    )

        rejection_reasons.append("; ".join(reasons))

    df["rejection_reason"] = rejection_reasons

    # Separate valid and rejected records
    rejected_mask = df["rejection_reason"] != ""

    valid_df = df[~rejected_mask].copy()
    rejected_df = df[rejected_mask].copy()

    # Calculate data quality score
    total_records = len(df)

    quality_score = (
        len(valid_df) / total_records * 100
        if total_records > 0 else 0
    )

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
