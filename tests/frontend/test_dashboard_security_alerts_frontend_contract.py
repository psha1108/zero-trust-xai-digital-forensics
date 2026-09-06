"""Frontend contract for persisted dashboard Security Alerts.

React consumes the backend Security Alerts API only. It must not fabricate
alerts, calculate risk, execute ML, or reproduce the Zero Trust policy.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


SERVICE = (
    ROOT
    / "security-frontend"
    / "src"
    / "services"
    / "dashboardService.js"
)


CARD = (
    ROOT
    / "security-frontend"
    / "src"
    / "components"
    / "dashboard"
    / "SecurityAlertsCard.jsx"
)


DASHBOARD = (
    ROOT
    / "security-frontend"
    / "src"
    / "pages"
    / "dashboard"
    / "Dashboard.jsx"
)


def _read(path: Path) -> str:
    return path.read_text(
        encoding="utf-8"
    )


def test_dashboard_service_calls_real_security_alerts_endpoint() -> None:
    source = _read(
        SERVICE
    )

    assert "getSecurityAlerts" in source

    assert (
        "axiosInstance.get('/dashboard/security-alerts')"
        in source
    )

    assert (
        "return response.data"
        in source
    )


def test_security_alerts_card_renders_backend_alert_contract() -> None:
    source = _read(
        CARD
    )

    required = (
        "dashboardService.getSecurityAlerts",
        "alert.event_id",
        "alert.timestamp",
        "alert.severity",
        "alert.alert_type",
        "alert.message",
        "alert.resource",
        "alert.policy_action",
        "alert.risk_score",
        "alert.privilege_mismatch",
    )

    for marker in required:
        assert marker in source


def test_security_alerts_card_handles_real_empty_array_without_fabrication() -> None:
    source = _read(
        CARD
    )

    assert (
        "Array.isArray(data)"
        in source
    )

    assert (
        "alerts.length === 0"
        in source
    )

    forbidden_fake_markers = (
        "Math.random",
        "fakeAlerts",
        "mockAlerts",
        "sampleAlerts",
        "dummyAlerts",
        "demoAlerts",
    )

    for marker in forbidden_fake_markers:
        assert marker not in source


def test_react_does_not_implement_security_decision_logic() -> None:
    card = _read(
        CARD
    )

    dashboard = _read(
        DASHBOARD
    )

    assert (
        "SecurityAlertsCard"
        in dashboard
    )

    assert (
        "<SecurityAlertsCard"
        in dashboard
    )

    forbidden_security_logic = (
        "analyze_operational_access",
        "score_operational_record",
        "classify_operational_record",
        "cluster_operational_record",
        "explain_random_forest_prediction",
        "decide_zero_trust_policy",
        "apply_zero_trust_policy",
        'decision === "Block"',
        'decision === "Restrict"',
        'decision === "OTP"',
    )

    for marker in forbidden_security_logic:
        assert marker not in card
