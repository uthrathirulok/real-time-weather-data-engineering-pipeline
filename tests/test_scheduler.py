import logging
from unittest.mock import patch

from scheduler import run_pipeline


def test_scheduler_handles_pipeline_failure(caplog):
    """Scheduler should catch and log pipeline failures."""

    with patch(
        "scheduler.main",
        side_effect=RuntimeError("Simulated pipeline failure")
    ):

        with caplog.at_level(logging.ERROR):
            run_pipeline()

    assert "Scheduled pipeline execution failed." in caplog.text
    assert "Simulated pipeline failure" in caplog.text


def test_scheduler_recovers_after_pipeline_failure(caplog):
    """A failed run should not prevent a subsequent successful run."""

    with patch(
        "scheduler.main",
        side_effect=[
            RuntimeError("Temporary failure"),
            None
        ]
    ) as mock_main:

        with caplog.at_level(logging.INFO):
            # First execution fails but is caught.
            run_pipeline()

            # Second execution succeeds.
            run_pipeline()

    assert mock_main.call_count == 2
    assert "Scheduled pipeline execution failed." in caplog.text
    assert "Scheduled pipeline execution completed." in caplog.text