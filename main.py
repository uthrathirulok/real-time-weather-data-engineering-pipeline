
import time
from datetime import datetime, timezone

from src.extract import extract_weather_data
from src.transform import transform_weather_data
from src.load import load_weather_data, load_rejected_records
from src.logger import get_logger
from src.monitoring import save_pipeline_run


logger = get_logger()


def main():

    start_time = time.perf_counter()
    started_at = datetime.now(timezone.utc)

    # Initialize monitoring values
    weather_records = []
    valid_df = None
    rejected_df = None
    inserted_count = 0
    rejected_count = 0
    quality_score = 0
    status = "FAILED"
    error_message = None

    logger.info("=" * 55)
    logger.info("WEATHER PIPELINE EXECUTION STARTED")

    try:
        print("=" * 55)
        print("REAL-TIME WEATHER DATA ENGINEERING PIPELINE")
        print("=" * 55)

        # STEP 1: EXTRACT
        print("\nSTEP 1: EXTRACTING WEATHER DATA")

        weather_records = extract_weather_data()

        # STEP 2: TRANSFORM
        print("\nSTEP 2: TRANSFORMING AND VALIDATING DATA")

        valid_df, rejected_df = transform_weather_data(
            weather_records
        )

        total_records = len(valid_df) + len(rejected_df)

        quality_score = (
            len(valid_df) / total_records * 100
            if total_records > 0 else 0
        )

        # STEP 3: LOAD VALID RECORDS
        print("\nSTEP 3: LOADING VALID DATA INTO POSTGRESQL")

        inserted_count = load_weather_data(valid_df)

        # STEP 4: SAVE REJECTED RECORDS
        print("\nSTEP 4: SAVING REJECTED RECORDS")

        rejected_count = load_rejected_records(rejected_df)

        # Mark pipeline as successful
        status = "SUCCESS"

        # PIPELINE SUMMARY
        print("\n" + "=" * 55)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 55)

        print(f"Records extracted: {len(weather_records)}")
        print(f"Valid records: {len(valid_df)}")
        print(f"Rejected records: {len(rejected_df)}")
        print(f"Rejected records saved: {rejected_count}")
        print(f"Records inserted: {inserted_count}")
        print(f"Data quality score: {quality_score:.2f}%")

        print("\nETL pipeline execution completed successfully!")

        logger.info("WEATHER PIPELINE EXECUTION COMPLETED SUCCESSFULLY")

    except Exception as error:

        error_message = str(error)

        logger.exception("WEATHER PIPELINE EXECUTION FAILED")

        raise

    finally:

        execution_time = time.perf_counter() - start_time
        finished_at = datetime.now(timezone.utc)

        logger.info(
            "Pipeline execution duration: %.2f seconds",
            execution_time
        )

        try:
            save_pipeline_run(
                started_at=started_at,
                finished_at=finished_at,
                execution_duration_seconds=execution_time,
                records_extracted=len(weather_records),
                records_valid=len(valid_df) if valid_df is not None else 0,
                records_rejected=len(rejected_df) if rejected_df is not None else 0,
                records_inserted=inserted_count,
                data_quality_score=quality_score,
                status=status,
                error_message=error_message
            )

        except Exception:
            logger.exception(
                "Could not save pipeline monitoring information."
            )


if __name__ == "__main__":
    main()
