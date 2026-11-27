
import pytest

from src.anomaly_detection import (
    evaluate_metric,
    detect_anomalies,
)


@pytest.fixture
def sample_rules():
    return {
        "enabled": True,
        "rules": {
            "data_quality_score": {
                "enabled": True,
                "warning_below": 95,
                "critical_below": 85,
            },
            "execution_duration_seconds": {
                "enabled": True,
                "warning_above": 30,
                "critical_above": 60,
            },
            "records_extracted": {
                "enabled": True,
                "warning_below": 3,
                "critical_below": 1,
            },
            "rejection_rate_percent": {
                "enabled": True,
                "warning_above": 5,
                "critical_above": 10,
            },
            "insertion_efficiency_percent": {
                "enabled": True,
                "warning_below": 90,
                "critical_below": 75,
            },
        },
    }


# --------------------------------------------------
# INDIVIDUAL METRIC TESTS
# --------------------------------------------------


@pytest.mark.parametrize(
    "metric,value,expected",
    [
        ("data_quality_score", 100, "NORMAL"),
        ("data_quality_score", 92, "WARNING"),
        ("data_quality_score", 80, "CRITICAL"),
        ("execution_duration_seconds", 20, "NORMAL"),
        ("execution_duration_seconds", 45, "WARNING"),
        ("execution_duration_seconds", 70, "CRITICAL"),
        ("records_extracted", 5, "NORMAL"),
        ("records_extracted", 2, "WARNING"),
        ("records_extracted", 0, "CRITICAL"),
        ("rejection_rate_percent", 2, "NORMAL"),
        ("rejection_rate_percent", 7, "WARNING"),
        ("rejection_rate_percent", 12, "CRITICAL"),
        ("insertion_efficiency_percent", 95, "NORMAL"),
        ("insertion_efficiency_percent", 80, "WARNING"),
        ("insertion_efficiency_percent", 60, "CRITICAL"),
    ],
)
def test_evaluate_metric_severity(
    sample_rules, metric, value, expected
):
    rule = sample_rules["rules"][metric]

    result = evaluate_metric(metric, value, rule)

    assert result["severity"] == expected
    assert result["metric"] == metric
    assert result["value"] == value
    assert result["message"]


# --------------------------------------------------
# THRESHOLD BOUNDARY TESTS
# --------------------------------------------------


def test_quality_score_exact_warning_threshold(sample_rules):
    rule = sample_rules["rules"]["data_quality_score"]

    result = evaluate_metric(
        "data_quality_score", 95, rule
    )

    assert result["severity"] == "NORMAL"


def test_quality_score_exact_critical_threshold(sample_rules):
    rule = sample_rules["rules"]["data_quality_score"]

    result = evaluate_metric(
        "data_quality_score", 85, rule
    )

    assert result["severity"] == "WARNING"


def test_duration_exact_warning_threshold(sample_rules):
    rule = sample_rules["rules"]["execution_duration_seconds"]

    result = evaluate_metric(
        "execution_duration_seconds", 30, rule
    )

    assert result["severity"] == "NORMAL"


def test_duration_exact_critical_threshold(sample_rules):
    rule = sample_rules["rules"]["execution_duration_seconds"]

    result = evaluate_metric(
        "execution_duration_seconds", 60, rule
    )

    assert result["severity"] == "WARNING"


# --------------------------------------------------
# DISABLED RULE TEST
# --------------------------------------------------


def test_disabled_metric_rule():
    rule = {
        "enabled": False,
        "warning_below": 95,
        "critical_below": 85,
    }

    result = evaluate_metric(
        "data_quality_score", 50, rule
    )

    assert result["severity"] == "DISABLED"


# --------------------------------------------------
# MISSING METRIC TEST
# --------------------------------------------------


def test_missing_metric_value():
    rule = {
        "enabled": True,
        "warning_below": 95,
        "critical_below": 85,
    }

    result = evaluate_metric(
        "data_quality_score", None, rule
    )

    assert result["severity"] == "UNKNOWN"


# --------------------------------------------------
# GLOBAL DISABLE TEST
# --------------------------------------------------


def test_global_anomaly_detection_disabled():
    config = {
        "enabled": False,
        "rules": {},
    }

    result = detect_anomalies({}, config)

    assert result["overall_status"] == "DISABLED"
    assert result["anomaly_count"] == 0
    assert result["results"] == []


# --------------------------------------------------
# INTEGRATED ENGINE TESTS
# --------------------------------------------------


def test_all_metrics_normal(sample_rules):
    metrics = {
        "data_quality_score": 100,
        "execution_duration_seconds": 10,
        "records_extracted": 5,
        "rejection_rate_percent": 0,
        "insertion_efficiency_percent": 100,
    }

    result = detect_anomalies(metrics, sample_rules)

    assert result["overall_status"] == "NORMAL"
    assert result["anomaly_count"] == 0
    assert result["total_metrics"] == 5


def test_warning_detected(sample_rules):
    metrics = {
        "data_quality_score": 92,
        "execution_duration_seconds": 10,
        "records_extracted": 5,
        "rejection_rate_percent": 0,
        "insertion_efficiency_percent": 100,
    }

    result = detect_anomalies(metrics, sample_rules)

    assert result["overall_status"] == "WARNING"
    assert result["anomaly_count"] == 1


def test_critical_overrides_warning(sample_rules):
    metrics = {
        "data_quality_score": 80,
        "execution_duration_seconds": 45,
        "records_extracted": 5,
        "rejection_rate_percent": 7,
        "insertion_efficiency_percent": 80,
    }

    result = detect_anomalies(metrics, sample_rules)

    assert result["overall_status"] == "CRITICAL"
    assert result["anomaly_count"] == 4


def test_missing_metrics_do_not_trigger_false_alerts(sample_rules):
    metrics = {
        "data_quality_score": None,
        "execution_duration_seconds": None,
        "records_extracted": None,
        "rejection_rate_percent": None,
        "insertion_efficiency_percent": None,
    }

    result = detect_anomalies(metrics, sample_rules)

    assert result["overall_status"] == "NORMAL"
    assert result["anomaly_count"] == 0

    assert all(
        item["severity"] == "UNKNOWN"
        for item in result["results"]
    )


def test_disabled_rule_ignored_in_overall_status(sample_rules):
    sample_rules["rules"]["data_quality_score"]["enabled"] = False

    metrics = {
        "data_quality_score": 50,
        "execution_duration_seconds": 10,
        "records_extracted": 5,
        "rejection_rate_percent": 0,
        "insertion_efficiency_percent": 100,
    }

    result = detect_anomalies(metrics, sample_rules)

    assert result["overall_status"] == "NORMAL"
    assert result["anomaly_count"] == 0

def test_all_metric_rules_disabled(sample_rules):
    for rule in sample_rules["rules"].values():
        rule["enabled"] = False

    metrics = {
        "data_quality_score": 100,
        "execution_duration_seconds": 10,
        "records_extracted": 5,
        "rejection_rate_percent": 0,
        "insertion_efficiency_percent": 100,
    }

    result = detect_anomalies(metrics, sample_rules)

    assert result["overall_status"] == "DISABLED"
    assert result["anomaly_count"] == 0
    assert result["total_metrics"] == 5
    assert all(
        item["severity"] == "DISABLED"
        for item in result["results"]
    )
    assert result["message"] == "All anomaly rules are disabled."

def test_anomaly_messages_explain_the_issue(sample_rules):
    metrics = {
        "data_quality_score": 80,
        "execution_duration_seconds": 70,
        "records_extracted": 0,
        "rejection_rate_percent": 12,
        "insertion_efficiency_percent": 60,
    }

    result = detect_anomalies(metrics, sample_rules)

    assert result["overall_status"] == "CRITICAL"

    for item in result["results"]:
        assert item["severity"] == "CRITICAL"
        assert item["message"]
        assert str(item["value"]) in item["message"]