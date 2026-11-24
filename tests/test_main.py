
import pandas as pd
import pytest

from unittest.mock import patch

from main import main


def create_extraction_result(
    records=None,
    successful_cities=None,
    failed_cities=None
):
    return {
        "records": records or [{"city": "Chennai"}],
        "successful_cities": successful_cities or ["Chennai"],
        "failed_cities": failed_cities or {}
    }


def create_dataframes():
    valid_df = pd.DataFrame([{"city": "Chennai"}])
    rejected_df = pd.DataFrame()
    return valid_df, rejected_df


@patch("main.save_pipeline_run")
@patch("main.load_rejected_records", return_value=0)
@patch("main.load_weather_data", return_value=1)
@patch("main.transform_weather_data")
@patch("main.extract_weather_data")
def test_pipeline_records_success_status(
    mock_extract,
    mock_transform,
    mock_load,
    mock_load_rejected,
    mock_monitor
):
    mock_extract.return_value = create_extraction_result()
    mock_transform.return_value = create_dataframes()

    main()

    assert mock_monitor.call_args.kwargs["status"] == "SUCCESS"


@patch("main.save_pipeline_run")
@patch("main.load_rejected_records", return_value=0)
@patch("main.load_weather_data", return_value=1)
@patch("main.transform_weather_data")
@patch("main.extract_weather_data")
def test_pipeline_records_partial_status(
    mock_extract,
    mock_transform,
    mock_load,
    mock_load_rejected,
    mock_monitor
):
    mock_extract.return_value = create_extraction_result(
        successful_cities=["Chennai", "Bengaluru"],
        failed_cities={"Delhi": "API request failed"}
    )
    mock_transform.return_value = create_dataframes()

    main()

    assert mock_monitor.call_args.kwargs["status"] == "PARTIAL"
    assert "Delhi" in mock_monitor.call_args.kwargs["error_message"]


@patch("main.save_pipeline_run")
@patch("main.extract_weather_data")
def test_pipeline_fails_when_all_cities_fail(
    mock_extract,
    mock_monitor
):
    mock_extract.return_value = {
        "records": [],
        "successful_cities": [],
        "failed_cities": {
            "Chennai": "API request failed",
            "Delhi": "API request failed"
        }
    }

    with pytest.raises(RuntimeError):
        main()

    assert mock_monitor.call_args.kwargs["status"] == "FAILED"

    error_message = mock_monitor.call_args.kwargs["error_message"]

    assert "Chennai" in error_message
    assert "Delhi" in error_message
    assert "API request failed" in error_message


@patch("main.save_pipeline_run")
@patch("main.load_rejected_records", return_value=0)
@patch("main.load_weather_data")
@patch("main.transform_weather_data")
@patch("main.extract_weather_data")
def test_pipeline_fails_when_database_loading_fails(
    mock_extract,
    mock_transform,
    mock_load,
    mock_load_rejected,
    mock_monitor
):
    mock_extract.return_value = create_extraction_result()
    mock_transform.return_value = create_dataframes()
    mock_load.side_effect = RuntimeError("Database loading failed")

    with pytest.raises(RuntimeError, match="Database loading failed"):
        main()

    assert mock_monitor.call_args.kwargs["status"] == "FAILED"
    assert (
        mock_monitor.call_args.kwargs["error_message"]
        == "Database loading failed"
    )


@patch("main.save_pipeline_run")
@patch("main.load_rejected_records", return_value=0)
@patch("main.load_weather_data")
@patch("main.transform_weather_data")
@patch("main.extract_weather_data")
def test_pipeline_preserves_partial_extraction_error_when_loading_fails(
    mock_extract,
    mock_transform,
    mock_load,
    mock_load_rejected,
    mock_monitor
):
    mock_extract.return_value = create_extraction_result(
        successful_cities=["Chennai"],
        failed_cities={"Delhi": "API request failed"}
    )

    mock_transform.return_value = create_dataframes()

    mock_load.side_effect = RuntimeError("Database loading failed")

    with pytest.raises(RuntimeError, match="Database loading failed"):
        main()

    assert mock_monitor.call_args.kwargs["status"] == "FAILED"

    error_message = mock_monitor.call_args.kwargs["error_message"]

    assert "Delhi" in error_message
    assert "API request failed" in error_message
    assert "Database loading failed" in error_message


@patch("main.save_pipeline_run")
@patch("main.load_rejected_records")
@patch("main.load_weather_data", return_value=1)
@patch("main.transform_weather_data")
@patch("main.extract_weather_data")
def test_pipeline_fails_when_rejected_record_loading_fails(
    mock_extract,
    mock_transform,
    mock_load,
    mock_load_rejected,
    mock_monitor
):
    mock_extract.return_value = create_extraction_result()

    valid_df = pd.DataFrame([{"city": "Chennai"}])
    rejected_df = pd.DataFrame([{"city": "InvalidCity"}])

    mock_transform.return_value = (valid_df, rejected_df)

    mock_load_rejected.side_effect = RuntimeError(
        "Rejected records loading failed"
    )

    with pytest.raises(
        RuntimeError,
        match="Rejected records loading failed"
    ):
        main()

    assert mock_monitor.call_args.kwargs["status"] == "FAILED"

    assert (
        mock_monitor.call_args.kwargs["error_message"]
        == "Rejected records loading failed"
    )
@patch("main.save_pipeline_run")
@patch("main.load_rejected_records", return_value=5)
@patch("main.load_weather_data", return_value=0)
@patch("main.transform_weather_data")
@patch("main.extract_weather_data")
def test_pipeline_records_partial_status_when_all_records_rejected(
    mock_extract,
    mock_transform,
    mock_load,
    mock_load_rejected,
    mock_monitor
):
    mock_extract.return_value = create_extraction_result(
        records=[
            {"city": "Chennai"},
            {"city": "Bengaluru"},
            {"city": "Mumbai"},
            {"city": "Delhi"},
            {"city": "Hyderabad"}
        ],
        successful_cities=[
            "Chennai",
            "Bengaluru",
            "Mumbai",
            "Delhi",
            "Hyderabad"
        ],
        failed_cities={}
    )

    valid_df = pd.DataFrame()
    rejected_df = pd.DataFrame([
        {"city": "Chennai"},
        {"city": "Bengaluru"},
        {"city": "Mumbai"},
        {"city": "Delhi"},
        {"city": "Hyderabad"}
    ])

    mock_transform.return_value = (valid_df, rejected_df)

    main()

    assert mock_monitor.call_args.kwargs["status"] == "PARTIAL"
    assert mock_monitor.call_args.kwargs["records_valid"] == 0
    assert mock_monitor.call_args.kwargs["records_rejected"] == 5
    assert mock_monitor.call_args.kwargs["data_quality_score"] == 0