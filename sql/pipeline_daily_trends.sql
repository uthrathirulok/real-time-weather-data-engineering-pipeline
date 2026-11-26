-- ============================================================
-- DAILY PIPELINE PERFORMANCE TRENDS
-- Historical reliability, runtime, and data volume
-- ============================================================

SELECT
    DATE(started_at AT TIME ZONE 'Asia/Kolkata') AS run_date,

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

    ROUND(
        AVG(execution_duration_seconds)::numeric,
        2
    ) AS avg_duration_seconds,

    ROUND(
        SUM(records_extracted)::numeric,
        2
    ) AS total_records_extracted,

    ROUND(
        SUM(records_inserted)::numeric,
        2
    ) AS total_records_inserted,

    ROUND(
        AVG(data_quality_score)::numeric,
        2
    ) AS avg_data_quality_score

FROM pipeline_runs

GROUP BY DATE(started_at AT TIME ZONE 'Asia/Kolkata')

ORDER BY run_date DESC;