"""Frontend contract for persisted dashboard Security State.

React is presentation only. It must fetch the read-only Flask
Security State endpoint and render persisted backend values without
calculating Zero Trust policy or fabricating ML results.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

BACKEND_DASHBOARD = (
    ROOT
    / "app"
    / "routes"
    / "dashboard.py"
)

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
    / "SecurityStateCard.jsx"
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


def test_backend_security_state_route_exists() -> None:
    source = _read(
        BACKEND_DASHBOARD
    )

    assert (
        '@dashboard_bp.route("/security-state", methods=["GET"])'
        in source
    )


def test_dashboard_service_calls_security_state_endpoint() -> None:
    source = _read(
        SERVICE
    )

    assert (
        "getSecurityState"
        in source
    )

    assert (
        "axiosInstance.get('/dashboard/security-state')"
        in source
        or
        'axiosInstance.get("/dashboard/security-state")'
        in source
    )


def test_security_state_card_renders_persisted_backend_fields() -> None:
    assert CARD.exists()

    source = _read(
        CARD
    )

    required = (
        "dashboardService.getSecurityState",
        "has_analysis",
        "risk_label",
        "risk_score",
        "anomaly_score",
        "cluster_id",
        "latest_action",
        "latest_resource",
        "privilege_mismatch",
        "is_active",
    )

    for marker in required:
        assert marker in source

    assert (
        "No security analysis available yet"
        in source
    )


def test_dashboard_replaces_risk_placeholder_with_security_state_card() -> None:
    source = _read(
        DASHBOARD
    )

    assert (
        "SecurityStateCard"
        in source
    )

    assert (
        "<SecurityStateCard"
        in source
    )

    assert (
        "Risk Analysis Not Available Yet"
        not in source
    )


def test_react_does_not_calculate_policy_or_fabricate_risk() -> None:
    assert CARD.exists()

    source = _read(
        CARD
    )

    forbidden = (
        "Math.random",
        "probability_high =",
        "risk_score =",
        "decide_zero_trust_policy",
        "apply_zero_trust_policy",
        "analyze_operational_access",
        "score_operational_record",
        "classify_operational_record",
        "cluster_operational_record",
        "explain_random_forest_prediction",
        'return "Allow"',
        'return "OTP"',
        'return "Restrict"',
        'return "Block"',
    )

    for marker in forbidden:
        assert marker not in source
