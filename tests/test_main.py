
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
