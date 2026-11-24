
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
    successful_cities = []
    failed_cities = {}

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

        extraction_result = extract_weather_data()

        weather_records = extraction_result["records"]
        successful_cities = extraction_result["successful_cities"]
        failed_cities = extraction_result["failed_cities"]

        print("\nEXTRACTION SUMMARY")
        print(f"Successful cities: {len(successful_cities)}")
        print(f"Failed cities: {len(failed_cities)}")

        if failed_cities:
            print("\nFailed city details:")

            for city, reason in failed_cities.items():
                print(f"- {city}: {reason}")

            error_message = "; ".join(
                f"{city}: {reason}"
                for city, reason in failed_cities.items()
            )

        # Stop if no city returned weather data

        if not weather_records:
            if error_message:
                raise RuntimeError(
                    f"Weather extraction failed for all configured cities. "
                    f"Details: {error_message}"
                )

            raise RuntimeError(
                "Weather extraction failed for all configured cities."
            )

        # Determine provisional extraction status
        status = (
            "PARTIAL"
            if failed_cities
            else "SUCCESS"
        )

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

        # Mark the run as partial if no records passed validation
        if len(valid_df) == 0 and weather_records:
            status = "PARTIAL"

        # STEP 3: LOAD VALID RECORDS
        print("\nSTEP 3: LOADING VALID DATA INTO POSTGRESQL")

        inserted_count = load_weather_data(valid_df)

        # STEP 4: SAVE REJECTED RECORDS
        print("\nSTEP 4: SAVING REJECTED RECORDS")

        rejected_count = load_rejected_records(rejected_df)

        # PIPELINE SUMMARY
        print("\n" + "=" * 55)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 55)

        print(f"Successful cities: {len(successful_cities)}")
        print(f"Failed cities: {len(failed_cities)}")
        print(f"Records extracted: {len(weather_records)}")
        print(f"Valid records: {len(valid_df)}")
        print(f"Rejected records: {len(rejected_df)}")
        print(f"Rejected records saved: {rejected_count}")
        print(f"Records inserted: {inserted_count}")
        print(f"Data quality score: {quality_score:.2f}%")
        print(f"Pipeline status: {status}")

        if status == "PARTIAL":
            print(
                "\nPipeline completed with partial extraction."
            )
            logger.warning(
                "WEATHER PIPELINE COMPLETED WITH PARTIAL STATUS"
            )
        else:
            print(
                "\nETL pipeline execution completed successfully!"
            )
            logger.info(
                "WEATHER PIPELINE EXECUTION COMPLETED SUCCESSFULLY"
            )


    except Exception as error:

        status = "FAILED"

        current_error = str(error)

        if error_message:
            error_message = f"{error_message}; Pipeline error: {current_error}"
        else:
            error_message = current_error

        logger.exception("WEATHER PIPELINE EXECUTION FAILED")

        print("\nETL pipeline execution failed.")

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
