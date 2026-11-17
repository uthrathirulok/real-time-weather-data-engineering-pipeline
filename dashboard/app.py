import sys
from pathlib import Path

import streamlit as st
import altair as alt
import pandas as pd
from sqlalchemy import text

# Add the main project folder to Python's import path
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.database import get_database_engine


def format_ist_timestamp(value, date_format="%d %b, %I:%M %p"):
    """Convert PostgreSQL timestamps to Indian Standard Time."""

    timestamp = pd.to_datetime(value, utc=True, errors="coerce")

    if pd.isna(timestamp):
        return "N/A"

    return timestamp.tz_convert("Asia/Kolkata").strftime(date_format)


@st.cache_data(ttl=30)
def get_rejected_record_count():
    """Count all rejected records stored in PostgreSQL."""

    engine = get_database_engine()

    query = text("""
        SELECT COUNT(*)
        FROM rejected_weather_records
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(query).scalar()

        return int(result or 0)

    finally:
        engine.dispose()


# --------------------------------------------------
# DASHBOARD CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Weather Data Pipeline Monitoring",
    page_icon="🌦️",
    layout="wide"
)


# --------------------------------------------------
# DATABASE FUNCTIONS
# --------------------------------------------------

@st.cache_data(ttl=30)
def get_latest_pipeline_run():
    """Fetch the latest pipeline execution from PostgreSQL."""

    engine = get_database_engine()

    query = text("""
        SELECT *
        FROM pipeline_runs
        ORDER BY id DESC
        LIMIT 1
    """)

    try:
        with engine.connect() as connection:
            result = pd.read_sql_query(query, connection)

        return result

    finally:
        engine.dispose()


@st.cache_data(ttl=60)
def get_latest_weather():
    """Fetch the latest weather observation for each city."""

    engine = get_database_engine()

    query = text("""
        SELECT DISTINCT ON (city)
            city,
            observation_time,
            temperature_2m,
            relative_humidity_2m,
            apparent_temperature,
            precipitation,
            wind_speed_10m
        FROM weather_records
        ORDER BY city, observation_time DESC;
    """)

    try:
        with engine.connect() as connection:
            result = pd.read_sql_query(query, connection)

        return result

    finally:
        engine.dispose()


@st.cache_data(ttl=60)
def get_historical_weather():
    """Retrieve historical weather observations from PostgreSQL."""

    engine = get_database_engine()

    query = text("""
        SELECT
            city,
            observation_time,
            temperature_2m,
            relative_humidity_2m,
            precipitation
        FROM weather_records
        ORDER BY observation_time ASC;
    """)

    try:
        with engine.connect() as connection:
            result = pd.read_sql_query(query, connection)

        return result

    finally:
        engine.dispose()


@st.cache_data(ttl=30)
def get_pipeline_history():
    """Retrieve recent pipeline execution history."""

    engine = get_database_engine()

    query = text("""
        SELECT
            id,
            started_at,
            records_extracted,
            records_valid,
            records_rejected,
            records_inserted,
            data_quality_score,
            status,
            execution_duration_seconds
        FROM pipeline_runs
        ORDER BY started_at DESC
        LIMIT 20;
    """)

    try:
        with engine.connect() as connection:
            result = pd.read_sql_query(query, connection)

        return result

    finally:
        engine.dispose()


@st.cache_data(ttl=30)
def get_rejected_records():
    """Retrieve rejected weather records from PostgreSQL."""

    engine = get_database_engine()

    query = text("""
        SELECT
            id,
            city,
            observation_time,
            temperature_2m,
            relative_humidity_2m,
            apparent_temperature,
            precipitation,
            weather_code,
            wind_speed_10m,
            rejection_reason,
            rejected_at
        FROM rejected_weather_records
        ORDER BY rejected_at DESC;
    """)

    try:
        with engine.connect() as connection:
            result = pd.read_sql_query(query, connection)

        return result

    finally:
        engine.dispose()


@st.cache_data(ttl=30)
def get_pipeline_analytics():
    """Retrieve pipeline metrics for historical performance analytics."""

    engine = get_database_engine()

    query = text("""
        SELECT
            id,
            started_at,
            status,
            records_extracted,
            records_valid,
            records_rejected,
            records_inserted,
            data_quality_score,
            execution_duration_seconds
        FROM pipeline_runs
        ORDER BY started_at ASC
    """)

    try:
        with engine.connect() as connection:
            result = pd.read_sql_query(query, connection)

        return result

    finally:
        engine.dispose()



# --------------------------------------------------
# DASHBOARD TITLE
# --------------------------------------------------

st.title("🌦️ Real-Time Weather Data Engineering Pipeline")

st.markdown(
    "Monitor weather data, pipeline execution, "
    "and data quality across five Indian cities."
)


# --------------------------------------------------
# PIPELINE HEALTH MONITORING
# --------------------------------------------------

st.divider()

st.header("❤️ Pipeline Health Monitoring")

try:
    latest_run = get_latest_pipeline_run()

    if latest_run.empty:

        st.warning("No pipeline execution records found yet.")

    else:

        run = latest_run.iloc[0]

        status = str(run["status"]).upper()

        if status == "SUCCESS":
            st.success("✅ Pipeline is running successfully!")

        elif status == "FAILED":
            st.error("❌ Latest pipeline execution failed!")

            if pd.notna(run.get("error_message")):
                st.write("Error details:", run["error_message"])

        else:
            st.warning(f"Pipeline status: {status}")

        last_execution = format_ist_timestamp(run["started_at"])

        quality_score = (
            f"{run['data_quality_score']:.2f}%"
            if pd.notna(run["data_quality_score"])
            else "N/A"
        )

        # DATA QUALITY ALERTS
        if pd.notna(run["data_quality_score"]):

            score = float(run["data_quality_score"])

            if score >= 100:
                st.success(
                    "Excellent! All records passed data quality validation."
                )

            elif score >= 90:
                st.warning(
                    f"Warning: Data quality is {score:.2f}%. "
                    "Some records need attention."
                )

            else:
                st.error(
                    f"Critical: Data quality is only {score:.2f}%. "
                    "Please investigate the rejected records."
                )

        else:
            st.info("Data quality score is not available.")

        duration = (
            f"{run['execution_duration_seconds']:.2f} sec"
            if pd.notna(run["execution_duration_seconds"])
            else "N/A"
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Pipeline Status", status)
        col2.metric("Data Quality Score", quality_score)
        col3.metric("Execution Duration", duration)
        col4.metric("Last Execution", last_execution)

        st.subheader("Latest Execution Statistics")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Records Extracted", int(run["records_extracted"]))
        col2.metric("Valid Records", int(run["records_valid"]))
        col3.metric("Rejected Records", int(run["records_rejected"]))
        col4.metric("Records Inserted", int(run["records_inserted"]))

except Exception as error:
    st.error(f"Unable to retrieve pipeline information: {error}")


# --------------------------------------------------
# LIVE WEATHER CONDITIONS
# --------------------------------------------------

st.divider()

st.header("🌍 Live Weather Conditions")

try:
    weather_df = get_latest_weather()

    if weather_df.empty:

        st.warning("No weather records found in the database.")

    else:

        columns = st.columns(5)

        for index, (_, row) in enumerate(weather_df.iterrows()):

            with columns[index % 5]:

                st.subheader(row["city"])

                st.metric(
                    "Temperature",
                    f"{row['temperature_2m']:.1f} °C"
                )

                st.metric(
                    "Humidity",
                    f"{row['relative_humidity_2m']:.0f}%"
                )

                st.metric(
                    "Feels Like",
                    f"{row['apparent_temperature']:.1f} °C"
                )

                st.metric(
                    "Wind Speed",
                    f"{row['wind_speed_10m']:.1f} km/h"
                )

                st.caption(
                    f"Observed: {row['observation_time']}"
                )

except Exception as error:
    st.error(f"Unable to retrieve weather data: {error}")


# --------------------------------------------------
# HISTORICAL WEATHER ANALYTICS
# --------------------------------------------------

st.divider()

st.header("📊 Historical Weather Analytics")

try:
    historical_df = get_historical_weather()

    if historical_df.empty:

        st.warning(
            "No historical weather records available yet. "
            "Run the pipeline again to collect more observations."
        )

    else:

        historical_df["observation_time"] = pd.to_datetime(
            historical_df["observation_time"]
        )

        st.subheader("🌡️ Temperature Trends")

        temperature_data = historical_df.pivot_table(
            index="observation_time",
            columns="city",
            values="temperature_2m",
            aggfunc="mean"
        )

        st.line_chart(temperature_data)

        st.subheader("💧 Humidity Trends")

        humidity_data = historical_df.pivot_table(
            index="observation_time",
            columns="city",
            values="relative_humidity_2m",
            aggfunc="mean"
        )

        st.line_chart(humidity_data)

        st.subheader("🌧️ Precipitation Comparison")

        precipitation_data = (
            historical_df.groupby("city")["precipitation"]
            .sum()
            .sort_values(ascending=False)
        )

        if precipitation_data.sum() == 0:

            st.info(
                "No precipitation recorded for any city "
                "during the available observation period."
            )

        else:

            st.bar_chart(precipitation_data)

        st.caption(
            "Total recorded precipitation by city (mm)."
        )

except Exception as error:
    st.error(
        f"Unable to retrieve historical weather data: {error}"
    )


# --------------------------------------------------
# REJECTED RECORDS DETAILS
# --------------------------------------------------

st.divider()

st.header("🚨 Rejected Records Details")

try:
    rejected_df = get_rejected_records()

    if rejected_df.empty:

        st.success(
            "No rejected weather records found. "
            "All available records passed validation!"
        )

    else:

        st.warning(
            f"{len(rejected_df)} rejected weather record(s) "
            "require attention."
        )

        # Rejected records summary
        col1, col2 = st.columns(2)

        col1.metric(
            "Total Rejected Records",
            len(rejected_df)
        )

        col2.metric(
            "Affected Cities",
            rejected_df["city"].nunique()
        )

        st.subheader("Rejected Records Table")

        st.dataframe(
            rejected_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": "Record ID",
                "city": "City",
                "observation_time": "Observation Time",
                "temperature_2m": "Temperature (°C)",
                "relative_humidity_2m": "Humidity (%)",
                "apparent_temperature": "Feels Like (°C)",
                "precipitation": "Precipitation (mm)",
                "weather_code": "Weather Code",
                "wind_speed_10m": "Wind Speed (km/h)",
                "rejection_reason": "Validation Failure Reason",
                "rejected_at": "Rejected At"
            }
        )

        st.subheader("Validation Failure Reasons")

        reason_counts = (
            rejected_df["rejection_reason"]
            .value_counts()
        )

        st.bar_chart(reason_counts)

except Exception as error:
    st.error(
        f"Unable to retrieve rejected records: {error}"
    )


# --------------------------------------------------
# DATA QUALITY & PIPELINE PERFORMANCE ANALYTICS
# --------------------------------------------------

st.divider()

st.header("📈 Data Quality & Pipeline Performance Analytics")

try:
    analytics_df = get_pipeline_analytics()

    if analytics_df.empty:
        st.info(
            "Pipeline analytics will appear after execution records "
            "are saved to PostgreSQL."
        )

    else:
        analytics_df["started_at"] = (
            pd.to_datetime(
                analytics_df["started_at"],
                utc=True,
                errors="coerce"
            )
            .dt.tz_convert("Asia/Kolkata")
            .dt.tz_localize(None)
        )

        analytics_df["status"] = (
            analytics_df["status"].astype(str).str.upper()
        )

        total_runs = len(analytics_df)
        successful_runs = int(
            (analytics_df["status"] == "SUCCESS").sum()
        )
        failed_runs = int(
            (analytics_df["status"] == "FAILED").sum()
        )

        success_rate = (
            successful_runs / total_runs * 100
            if total_runs else 0
        )

        average_duration = analytics_df[
            "execution_duration_seconds"
        ].dropna().mean()

        pipeline_rejected_total = int(
            pd.to_numeric(
                analytics_df["records_rejected"],
                errors="coerce"
            ).fillna(0).sum()
        )

        rejected_records_in_db = get_rejected_record_count()

        metric1, metric2, metric3, metric4, metric5 = st.columns(5)

        metric1.metric("Total Pipeline Runs", total_runs)
        metric2.metric("Successful Runs", successful_runs)
        metric3.metric("Success Rate", f"{success_rate:.1f}%")
        metric4.metric("Rejected by Pipeline Runs", pipeline_rejected_total)
        metric5.metric("Rejected Records Stored", rejected_records_in_db)

        st.caption(
            "Rejected by Pipeline Runs represents the sum recorded in "
            "pipeline_runs. Rejected Records Stored represents the current "
            "number of rows in rejected_weather_records, including test records."
        )

        if failed_runs > 0:
            st.warning(
                f"{failed_runs} failed pipeline execution(s) found. "
                "Review the execution history and application logs."
            )
        else:
            st.success(
                "No failed pipeline executions found in the recorded history."
            )

        if pd.notna(average_duration):
            st.caption(
                f"Average execution duration: {average_duration:.2f} seconds"
            )

        
        # Data quality score over time
        st.subheader("Data Quality Score Trend")

        quality_df = analytics_df[
            ["started_at", "data_quality_score"]
        ].dropna().copy()

        if not quality_df.empty:
            quality_df["started_at"] = pd.to_datetime(
                quality_df["started_at"], errors="coerce"
            )

            quality_df["data_quality_score"] = pd.to_numeric(
                quality_df["data_quality_score"], errors="coerce"
            )

            quality_df = quality_df.dropna().sort_values("started_at")

            quality_chart = alt.Chart(quality_df).mark_line(
                point=True
            ).encode(
                x=alt.X(
                    "started_at:T",
                    title="Pipeline Execution Time"
                ),
                y=alt.Y(
                    "data_quality_score:Q",
                    title="Data Quality Score (%)",
                    scale=alt.Scale(domain=[0, 100])
                ),
                tooltip=[
                    alt.Tooltip("started_at:T", title="Started At"),
                    alt.Tooltip(
                        "data_quality_score:Q",
                        title="Quality Score",
                        format=".2f"
                    )
                ]
            ).properties(height=350)

            st.altair_chart(
                quality_chart,
                use_container_width=True
            )

            st.caption(
                "Tracks the percentage of extracted records that passed validation "
                "for each pipeline execution."
            )
        else:
            st.info("No data quality scores are available yet.")

        
        # Pipeline execution duration over time
        st.subheader("Pipeline Execution Duration")

        duration_df = analytics_df[
            ["started_at", "execution_duration_seconds"]
        ].dropna()

        if not duration_df.empty:
            duration_chart = duration_df.set_index("started_at")
            st.line_chart(duration_chart)
            st.caption(
                "Shows how long each pipeline execution took, in seconds."
            )
        else:
            st.info("No execution duration measurements are available yet.")

        # Records extracted, valid, rejected and inserted
        st.subheader("Record Processing Trends")

        records_df = analytics_df[
            [
                "id",
                "records_extracted",
                "records_valid",
                "records_rejected",
                "records_inserted",
            ]
        ].copy()

        count_columns = [
            "records_extracted",
            "records_valid",
            "records_rejected",
            "records_inserted",
        ]

        for column in count_columns:
            records_df[column] = (
                pd.to_numeric(records_df[column], errors="coerce")
                .fillna(0)
                .clip(lower=0)
            )

        records_df["Run"] = records_df["id"].apply(
            lambda run_id: f"Run {int(run_id)}"
        )

        records_chart = records_df.set_index("Run")[count_columns]

        if not records_chart.empty:
            st.bar_chart(records_chart)
            st.caption(
                "Compares extracted, valid, rejected and inserted record "
                "counts for each pipeline Run ID."
            )

        # Success and failure distribution
        st.subheader("Pipeline Run Status Distribution")

        status_counts = analytics_df["status"].value_counts()

        if not status_counts.empty:
            st.bar_chart(status_counts)

        st.caption(
            "Execution metrics and trends are calculated from pipeline_runs. "
            "The stored rejected-record count is queried separately from "
            "rejected_weather_records in PostgreSQL."
        )
        
except Exception as error:
    st.error(
        f"Unable to retrieve pipeline performance analytics: {error}"
    )



# --------------------------------------------------
# PIPELINE EXECUTION HISTORY
# --------------------------------------------------

st.divider()

st.header("📋 Pipeline Execution History")

try:
    history_df = get_pipeline_history()

    if not history_df.empty:
        history_df["started_at"] = history_df["started_at"].apply(
            lambda value: format_ist_timestamp(
                value,
                "%d %b %Y, %I:%M %p"
            )
        )

    if history_df.empty:

        st.info("No pipeline execution history available.")

    else:

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": "Run ID",
                "started_at": "Execution Time",
                "records_extracted": "Extracted",
                "records_valid": "Valid",
                "records_rejected": "Rejected",
                "records_inserted": "Inserted",
                "data_quality_score": st.column_config.NumberColumn(
                    "Quality Score (%)",
                    format="%.2f"
                ),
                "status": "Status",
                "execution_duration_seconds": st.column_config.NumberColumn(
                    "Duration (seconds)",
                    format="%.2f"
                )
            }
        )

        st.caption("Showing the latest 20 pipeline executions.")

except Exception as error:
    st.error(f"Unable to retrieve pipeline history: {error}")