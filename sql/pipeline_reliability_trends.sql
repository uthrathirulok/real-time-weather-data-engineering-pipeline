
-- ============================================================
-- DAILY PIPELINE RELIABILITY TRENDS
-- Tracks successful, partial, and failed runs over time.
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
        (
            COUNT(*) FILTER (WHERE status IN ('PARTIAL', 'FAILED')) * 100.0
            / NULLIF(COUNT(*), 0)
        )::numeric,
        2
    ) AS incident_rate_percent,

    ROUND(
        (
            COUNT(*) FILTER (WHERE status = 'FAILED') * 100.0
            / NULLIF(COUNT(*), 0)
        )::numeric,
        2
    ) AS failure_rate_percent,

    ROUND(
        AVG(execution_duration_seconds)::numeric,
        2
    ) AS avg_duration_seconds

FROM pipeline_runs

GROUP BY DATE(started_at AT TIME ZONE 'Asia/Kolkata')

ORDER BY run_date DESC;
