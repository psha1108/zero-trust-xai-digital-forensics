"""Static contract for persisted Security Alerts.

Security Alerts are a read-only projection of existing AccessEvent rows.
The endpoint must not execute ML, SHAP, or the Zero Trust policy engine.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

DASHBOARD = (
    ROOT
    / "app"
    / "routes"
    / "dashboard.py"
)


ROUTE_MARKER = (
    '@dashboard_bp.route("/security-alerts", methods=["GET"])'
)


def _read_dashboard() -> str:
    return DASHBOARD.read_text(
        encoding="utf-8"
    )


def _security_alerts_source() -> str:
    source = _read_dashboard()

    if ROUTE_MARKER not in source:
        return ""

    start = source.index(
        ROUTE_MARKER
    )

    tail = source[start:]

    next_route = tail.find(
        "\n@dashboard_bp.route(",
        len(ROUTE_MARKER),
    )

    if next_route == -1:
        return tail

    return tail[:next_route]


def test_security_alerts_route_requires_authentication() -> None:
    source = _read_dashboard()
    function = _security_alerts_source()

    assert ROUTE_MARKER in source
    assert "@login_required" in function
    assert "def security_alerts():" in function


def test_security_alerts_use_only_current_users_access_events() -> None:
    function = _security_alerts_source()

    required = (
        "AccessEvent.query",
        ".filter_by(",
        "user_id=current_user.id",
        "event.decision",
        "event.privilege_mismatch",
    )

    for marker in required:
        assert marker in function

    assert "LoginEvent.query" not in function
    assert "Session.query" not in function


def test_security_alerts_use_frozen_persisted_alert_rules() -> None:
    function = _security_alerts_source()

    required = (
        'if decision == "Block":',
        'elif decision == "Restrict":',
        "elif event.privilege_mismatch:",
        'elif decision == "OTP":',
        '"SESSION_BLOCKED"',
        '"ACCESS_RESTRICTED"',
        '"PRIVILEGE_MISMATCH"',
        '"OTP_REQUIRED"',
        '"critical"',
        '"high"',
        '"medium"',
    )

    for marker in required:
        assert marker in function

    block = function.index(
        'if decision == "Block":'
    )

    restrict = function.index(
        'elif decision == "Restrict":'
    )

    mismatch = function.index(
        "elif event.privilege_mismatch:"
    )

    otp = function.index(
        'elif decision == "OTP":'
    )

    assert block < restrict < mismatch < otp


def test_security_alerts_are_newest_first_and_limited_to_twenty() -> None:
    function = _security_alerts_source()

    required = (
        ".order_by(",
        "AccessEvent.timestamp.desc()",
        ".limit(20)",
        "alerts = []",
        "alerts.append(",
    )

    for marker in required:
        assert marker in function

    forbidden = (
        "analyze_operational_access",
        "score_operational_record",
        "classify_operational_record",
        "cluster_operational_record",
        "explain_random_forest_prediction",
        "decide_zero_trust_policy",
        "apply_zero_trust_policy",
    )

    for marker in forbidden:
        assert marker not in function


def test_security_alerts_return_exact_persisted_event_fields() -> None:
    function = _security_alerts_source()

    required_fields = (
        '"event_id"',
        '"timestamp"',
        '"severity"',
        '"alert_type"',
        '"message"',
        '"resource"',
        '"policy_action"',
        '"risk_score"',
        '"privilege_mismatch"',
        '"session_id"',
    )

    for field in required_fields:
        assert field in function

    required_semantics = (
        "event.id",
        "event.timestamp.isoformat()",
        "event.resource",
        "event.decision",
        "event.risk_score",
        "event.privilege_mismatch",
        "event.session_id",
        "return jsonify(alerts), 200",
    )

    for marker in required_semantics:
        assert marker in function
