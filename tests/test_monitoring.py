
from unittest.mock import MagicMock, patch

import pytest

from src.monitoring import save_pipeline_run


def create_monitoring_parameters():
    """Create sample pipeline execution details."""

    return {
        "started_at": "2026-11-18 10:00:00+00:00",
        "finished_at": "2026-11-18 10:00:05+00:00",
        "execution_duration_seconds": 5.0,
        "records_extracted": 5,
        "records_valid": 4,
        "records_rejected": 1,
        "records_inserted": 4,
        "data_quality_score": 80.0,
        "status": "SUCCESS",
        "error_message": None
    }


@patch("src.monitoring.get_database_engine")
def test_save_pipeline_run_success(mock_get_engine):

    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine

    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 101

    mock_connection = MagicMock()
    mock_connection.execute.return_value = mock_result

    mock_engine.begin.return_value.__enter__.return_value = mock_connection

    parameters = create_monitoring_parameters()

    run_id = save_pipeline_run(**parameters)

    assert run_id == 101

    mock_connection.execute.assert_called_once()
    mock_engine.dispose.assert_called_once()


@patch("src.monitoring.get_database_engine")
def test_save_pipeline_run_database_failure(mock_get_engine):

    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine

    mock_engine.begin.side_effect = RuntimeError(
        "Simulated database failure"
    )

    parameters = create_monitoring_parameters()

    with pytest.raises(RuntimeError, match="Simulated database failure"):
        save_pipeline_run(**parameters)

    mock_engine.dispose.assert_called_once()


@patch("src.monitoring.get_database_engine")
def test_save_pipeline_run_engine_creation_failure(mock_get_engine):

    mock_get_engine.side_effect = RuntimeError(
        "Engine creation failed"
    )

    parameters = create_monitoring_parameters()

    with pytest.raises(RuntimeError, match="Engine creation failed"):
        save_pipeline_run(**parameters)


@patch("src.monitoring.get_database_engine")
def test_save_pipeline_run_with_partial_status(mock_get_engine):

    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine

    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 102

    mock_connection = MagicMock()
    mock_connection.execute.return_value = mock_result

    mock_engine.begin.return_value.__enter__.return_value = mock_connection

    parameters = create_monitoring_parameters()
    parameters["status"] = "PARTIAL"
    parameters["error_message"] = "Delhi API request failed"

    run_id = save_pipeline_run(**parameters)

    assert run_id == 102

    mock_connection.execute.assert_called_once()

    saved_parameters = (
        mock_connection.execute.call_args.args[1]
    )

    assert saved_parameters["status"] == "PARTIAL"
    assert saved_parameters["error_message"] == (
        "Delhi API request failed"
    )

    assert saved_parameters["records_extracted"] == 5
    assert saved_parameters["records_valid"] == 4
    assert saved_parameters["records_rejected"] == 1
    assert saved_parameters["records_inserted"] == 4

    mock_engine.dispose.assert_called_once()