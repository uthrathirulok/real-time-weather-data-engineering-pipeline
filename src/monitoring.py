
from sqlalchemy import text

from src.database import get_database_engine
from src.logger import get_logger


logger = get_logger()


def save_pipeline_run(
    started_at,
    finished_at,
    execution_duration_seconds,
    records_extracted=0,
    records_valid=0,
    records_rejected=0,
    records_inserted=0,
    data_quality_score=None,
    status="SUCCESS",
    error_message=None
):
    """
    Save pipeline execution details into PostgreSQL.
    """

    engine = None

    insert_query = text("""
        INSERT INTO pipeline_runs (
            started_at,
            finished_at,
            execution_duration_seconds,
            records_extracted,
            records_valid,
            records_rejected,
            records_inserted,
            data_quality_score,
            status,
            error_message
        )
        VALUES (
            :started_at,
            :finished_at,
            :execution_duration_seconds,
            :records_extracted,
            :records_valid,
            :records_rejected,
            :records_inserted,
            :data_quality_score,
            :status,
            :error_message
        )
        RETURNING id
    """)

    parameters = {
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_duration_seconds": execution_duration_seconds,
        "records_extracted": records_extracted,
        "records_valid": records_valid,
        "records_rejected": records_rejected,
        "records_inserted": records_inserted,
        "data_quality_score": data_quality_score,
        "status": status,
        "error_message": error_message
    }

    try:
        engine = get_database_engine()

        with engine.begin() as connection:
            result = connection.execute(
                insert_query,
                parameters
            )

            run_id = result.scalar_one()

        logger.info(
            "Pipeline monitoring record saved. Run ID: %d",
            run_id
        )

        print(f"Pipeline monitoring record saved. Run ID: {run_id}")

        return run_id

    except Exception:
        logger.exception("Failed to save pipeline monitoring record")
        raise

    finally:
        if engine is not None:
            engine.dispose()
