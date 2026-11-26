
-- ============================================================
-- UNIFIED PIPELINE ANALYTICS SUMMARY
-- Consolidates performance, reliability, and data quality KPIs.
-- Read-only analytics query.
-- ============================================================

SELECT
    COUNT(*) AS total_pipeline_runs,

    COUNT(*) FILTER (
        WHERE status = 'SUCCESS'
    ) AS successful_runs,

    COUNT(*) FILTER (
        WHERE status = 'PARTIAL'
    ) AS partial_runs,

    COUNT(*) FILTER (
        WHERE status = 'FAILED'
    ) AS failed_runs,

    ROUND(
        (
            COUNT(*) FILTER (WHERE status = 'SUCCESS') * 100.0
            / NULLIF(COUNT(*), 0)
        )::numeric,
        2
    ) AS overall_success_rate_percent,

    ROUND(
        AVG(execution_duration_seconds)::numeric,
        2
    ) AS avg_execution_duration_seconds,

    ROUND(
        MIN(execution_duration_seconds)::numeric,
        2
    ) AS fastest_run_seconds,

    ROUND(
        MAX(execution_duration_seconds)::numeric,
        2
    ) AS slowest_run_seconds,

    SUM(records_extracted) AS total_records_extracted,

    SUM(records_valid) AS total_records_valid,

    SUM(records_rejected) AS total_records_rejected,

    SUM(records_inserted) AS total_records_inserted,

    ROUND(
        AVG(data_quality_score)::numeric,
        2
    ) AS avg_data_quality_score,

    ROUND(
        (
            SUM(records_rejected) * 100.0
            / NULLIF(SUM(records_valid + records_rejected), 0)
        )::numeric,
        2
    ) AS overall_rejection_rate_percent,
     
    
    ROUND(
        (
            SUM(records_inserted)::numeric
            / NULLIF(SUM(execution_duration_seconds)::numeric, 0)
        ),
        2
    ) AS overall_records_per_second

FROM pipeline_runs;
