"""Static contract for the dashboard Security State endpoint.

The dashboard must display already-persisted Zero Trust and operational
ML state. Reading this endpoint must never execute ML, execute policy,
or mutate the database.
"""

from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[2]

DASHBOARD_PATH = (
    ROOT
    / "app"
    / "routes"
    / "dashboard.py"
)

MODELS_PATH = (
    ROOT
    / "app"
    / "models.py"
)


EXPECTED_FIELDS = {
    "session_id",
    "risk_label",
    "risk_score",
    "anomaly_score",
    "cluster_id",
    "latest_action",
    "latest_resource",
    "latest_access_at",
    "privilege_mismatch",
    "is_active",
    "has_analysis",
}


def _read(path: Path) -> str:
    return path.read_text(
        encoding="utf-8"
    )


def _security_state_source() -> str:
    source = _read(
        DASHBOARD_PATH
    )

    tree = ast.parse(
        source
    )

    for node in tree.body:
        if (
            isinstance(
                node,
                ast.FunctionDef,
            )
            and node.name == "security_state"
        ):
            segment = ast.get_source_segment(
                source,
                node,
            )

            assert segment is not None

            return segment

    raise AssertionError(
        "security_state function is not implemented."
    )


def test_persisted_security_state_fields_exist() -> None:
    source = _read(
        MODELS_PATH
    )

    required = {
        "current_risk_score",
        "current_risk_label",
        "anomaly_score",
        "risk_label",
        "cluster_id",
        "decision",
        "risk_score",
        "privilege_mismatch",
        "is_active",
    }

    missing = {
        term
        for term in required
        if term not in source
    }

    assert not missing


def test_security_state_route_is_authenticated() -> None:
    source = _read(
        DASHBOARD_PATH
    )

    assert (
        '@dashboard_bp.route("/security-state", methods=["GET"])'
        in source
    )

    route_index = source.index(
        '@dashboard_bp.route("/security-state", methods=["GET"])'
    )

    function_index = source.index(
        "def security_state()",
        route_index,
    )

    decorator_region = source[
        route_index:function_index
    ]

    assert (
        "@login_required"
        in decorator_region
    )


def test_security_state_response_contract_is_exact() -> None:
    source = _security_state_source()

    for field in EXPECTED_FIELDS:
        assert (
            f'"{field}"'
            in source
            or f"'{field}'"
            in source
        )

    forbidden_extra_security_outputs = {
        "shap",
        "explanation",
        "probability_low",
        "probability_medium",
    }

    lowered = source.lower()

    for forbidden in forbidden_extra_security_outputs:
        assert forbidden not in lowered


def test_security_state_reads_current_persisted_session_only() -> None:
    source = _security_state_source()

    required = (
        'flask_session.get("app_session_id")',
        "Session.query",
        "filter_by(",
        "session_id=app_session_id",
        "AccessEvent.query",
        "session_id=session_row.session_id",
        "AccessEvent.timestamp.desc()",
        "session_row.login_event",
    )

    for marker in required:
        assert marker in source


def test_security_state_does_not_execute_or_mutate_security_logic() -> None:
    source = _security_state_source()

    forbidden = (
        "analyze_operational_access",
        "score_operational_record",
        "classify_operational_record",
        "cluster_operational_record",
        "explain_random_forest_prediction",
        "apply_zero_trust_policy",
        "decide_zero_trust_policy",
        "create_otp_challenge",
        "db.session.add",
        "db.session.delete",
        "db.session.flush",
        "db.session.commit",
    )

    for marker in forbidden:
        assert marker not in source
