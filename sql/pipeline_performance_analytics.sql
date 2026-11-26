-- ============================================================
-- PIPELINE PERFORMANCE ANALYTICS
-- Historical execution metrics and operational performance
-- ============================================================

SELECT
    COUNT(*) AS total_runs,

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
    ) AS success_rate_percent,

    ROUND(AVG(execution_duration_seconds)::numeric, 2)
        AS avg_duration_seconds,

    ROUND(MIN(execution_duration_seconds)::numeric, 2)
        AS fastest_run_seconds,

    ROUND(MAX(execution_duration_seconds)::numeric, 2)
        AS slowest_run_seconds,

    ROUND(AVG(records_extracted)::numeric, 2)
        AS avg_records_extracted,

    ROUND(AVG(records_inserted)::numeric, 2)
        AS avg_records_inserted,

    ROUND(AVG(data_quality_score)::numeric, 2)
        AS avg_data_quality_score,

    ROUND(
        (
            SUM(records_rejected)::numeric * 100
            / NULLIF(SUM(records_valid + records_rejected), 0)
        ),
        2
    ) AS rejection_rate_percent,

    ROUND(
        AVG(
            records_inserted::numeric
            / NULLIF(execution_duration_seconds::numeric, 0)
        ),
        2
    ) AS avg_records_per_second

FROM pipeline_runs;