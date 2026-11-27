
import json
from pathlib import Path


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "anomaly_rules.json"
)


def load_anomaly_rules(config_path=None):
    """Load anomaly detection rules from JSON configuration."""

    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    with open(path, "r", encoding="utf-8") as file:
        config = json.load(file)

    return config


# --------------------------------------------------
# ANOMALY DETECTION ENGINE
# --------------------------------------------------

SEVERITY_LEVELS = {
    "NORMAL": 0,
    "WARNING": 1,
    "CRITICAL": 2
}


def evaluate_metric(metric_name, value, rule):
    """Evaluate one metric against its configured thresholds."""

    if not rule.get("enabled", True):
        return {
            "metric": metric_name,
            "value": value,
            "severity": "DISABLED",
            "message": "This anomaly rule is disabled."
        }

    if value is None:
        return {
            "metric": metric_name,
            "value": None,
            "severity": "UNKNOWN",
            "message": "Metric value is unavailable."
        }

    severity = "NORMAL"
    message = "Metric is within normal thresholds."

    # Metrics where lower values indicate a problem
    if "warning_below" in rule and "critical_below" in rule:

        if value < rule["critical_below"]:
            severity = "CRITICAL"
            message = (
                f"{metric_name} is critically low: {value}, "
                f"below {rule['critical_below']}."
            )

        elif value < rule["warning_below"]:
            severity = "WARNING"
            message = (
                f"{metric_name} is low: {value}, "
                f"below {rule['warning_below']}."
            )

    # Metrics where higher values indicate a problem
    elif "warning_above" in rule and "critical_above" in rule:

        if value > rule["critical_above"]:
            severity = "CRITICAL"
            message = (
                f"{metric_name} is critically high: {value}, "
                f"above {rule['critical_above']}."
            )

        elif value > rule["warning_above"]:
            severity = "WARNING"
            message = (
                f"{metric_name} is high: {value}, "
                f"above {rule['warning_above']}."
            )

    return {
        "metric": metric_name,
        "value": value,
        "severity": severity,
        "message": message
    }


# --------------------------------------------------
# EVALUATE ALL CONFIGURED METRICS
# --------------------------------------------------

def detect_anomalies(metrics, config=None):
    """Evaluate all metrics and return anomaly detection results."""

    if config is None:
        config = load_anomaly_rules()

    if not config.get("enabled", True):
        return {
            "overall_status": "DISABLED",
            "total_metrics": 0,
            "anomaly_count": 0,
            "results": [],
            "message": "Anomaly detection is globally disabled."
        }

    rules = config.get("rules", {})
    results = []

    for metric_name, rule in rules.items():

        value = metrics.get(metric_name)

        result = evaluate_metric(
            metric_name,
            value,
            rule
        )

        results.append(result)

    # Determine the overall severity
    overall_status = "NORMAL"

    for result in results:
        severity = result["severity"]

        if severity in SEVERITY_LEVELS:

            if (
                SEVERITY_LEVELS[severity]
                > SEVERITY_LEVELS[overall_status]
            ):
                overall_status = severity

        anomaly_count = sum(
        1
        for result in results
        if result["severity"] in ("WARNING", "CRITICAL")
    )

    # Check whether at least one metric rule is actively monitored
    active_rule_count = sum(
        1
        for rule in rules.values()
        if rule.get("enabled", True)
    )

    if active_rule_count == 0:
        overall_status = "DISABLED"

    if overall_status == "DISABLED":
        message = "All anomaly rules are disabled."
    elif anomaly_count > 0:
        message = "Anomalies detected."
    else:
        message = "All monitored metrics are normal."

    return {
        "overall_status": overall_status,
        "total_metrics": len(results),
        "anomaly_count": anomaly_count,
        "results": results,
        "message": message
    }