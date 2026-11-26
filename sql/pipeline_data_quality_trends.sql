
-- ============================================================
-- DAILY DATA QUALITY TRENDS
-- Tracks valid records, rejected records, rejection rates,
-- and data quality scores over time.
-- ============================================================

SELECT
    DATE(started_at AT TIME ZONE 'Asia/Kolkata') AS run_date,

    COUNT(*) AS total_runs,

    SUM(records_extracted) AS total_records_extracted,

    SUM(records_valid) AS total_records_valid,

    SUM(records_rejected) AS total_records_rejected,

    ROUND(
        (
            SUM(records_rejected) * 100.0
            / NULLIF(SUM(records_valid + records_rejected), 0)
        )::numeric,
        2
    ) AS rejection_rate_percent,

    ROUND(
        AVG(data_quality_score)::numeric,
        2
    ) AS avg_data_quality_score,

    MIN(data_quality_score) AS min_data_quality_score,

    MAX(data_quality_score) AS max_data_quality_score

FROM pipeline_runs

GROUP BY DATE(started_at AT TIME ZONE 'Asia/Kolkata')

ORDER BY run_date DESC;
