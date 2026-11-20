
-- ============================================================
-- REAL-TIME WEATHER DATA ENGINEERING PIPELINE
-- PostgreSQL Database Schema
-- ============================================================

-- 1. WEATHER RECORDS
CREATE TABLE IF NOT EXISTS weather_records (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    observation_time TIMESTAMP NOT NULL,
    temperature_2m DOUBLE PRECISION,
    relative_humidity_2m DOUBLE PRECISION,
    apparent_temperature DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    weather_code INTEGER,
    wind_speed_10m DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_city_observation
        UNIQUE (city, observation_time)
);


-- 2. REJECTED WEATHER RECORDS
CREATE TABLE IF NOT EXISTS rejected_weather_records (
    id BIGSERIAL PRIMARY KEY,
    city VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    observation_time TIMESTAMP,
    temperature_2m DOUBLE PRECISION,
    relative_humidity_2m DOUBLE PRECISION,
    apparent_temperature DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    weather_code INTEGER,
    wind_speed_10m DOUBLE PRECISION,
    rejection_reason TEXT NOT NULL,
    rejected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 3. PIPELINE RUN MONITORING
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    finished_at TIMESTAMP WITH TIME ZONE,
    execution_duration_seconds DOUBLE PRECISION,
    records_extracted INTEGER DEFAULT 0,
    records_valid INTEGER DEFAULT 0,
    records_rejected INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    data_quality_score NUMERIC(5, 2),
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     
    CONSTRAINT valid_pipeline_status
    CHECK (status IN ('SUCCESS', 'PARTIAL', 'FAILED')),

    CONSTRAINT valid_quality_score
        CHECK (
            data_quality_score IS NULL
            OR (
                data_quality_score >= 0
                AND data_quality_score <= 100
            )
        )
);
