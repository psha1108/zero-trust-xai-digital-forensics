"""Contract tests for triggering RF + SHAP after Flask access logging."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask

from app.routes import resources


def test_log_and_analyze_uses_exact_committed_access_event(
    monkeypatch,
) -> None:
    event = SimpleNamespace(
        id=42,
        session_id="session-123",
    )

    analysis = {
        "features": {"role": "employee"},
        "prediction": {
            "predicted_risk": "medium",
        },
        "explanation": {
            "prediction": "medium",
        },
    }

    observed = {
        "logged_resource": None,
        "session_id": None,
        "access_event_id": None,
    }

    def fake_log_access(resource):
        observed["logged_resource"] = resource
        return event

    def fake_analyze(
        *,
        session_id,
        access_event_id,
    ):
        observed["session_id"] = session_id
        observed["access_event_id"] = access_event_id
        return analysis

    monkeypatch.setattr(
        resources,
        "_log_access",
        fake_log_access,
    )

    monkeypatch.setattr(
        resources,
        "analyze_operational_access",
        fake_analyze,
        raising=False,
    )

    helper = getattr(
        resources,
        "_log_and_analyze_access",
        None,
    )

    assert callable(helper), (
        "_log_and_analyze_access must exist."
    )

    returned_event, returned_analysis = helper(
        "finance_page"
    )

    assert observed == {
        "logged_resource": "finance_page",
        "session_id": "session-123",
        "access_event_id": 42,
    }

    assert returned_event is event
    assert returned_analysis is analysis


def test_resource_response_uses_combined_log_and_analysis_helper(
    monkeypatch,
) -> None:
    app = Flask(
        "resource-analysis-trigger-test"
    )

    observed = []

    event = SimpleNamespace(
        id=10,
        session_id="session-normal",
    )

    analysis = {
        "prediction": {
            "predicted_risk": "low",
            "probability_low": 0.95,
            "probability_medium": 0.03,
            "probability_high": 0.02,
        },
        "anomaly_detection": {
            "is_anomaly": False,
        },
        "behavioral_cluster": {
            "cluster_id": 1,
        },
    }

    policy_result = {
        "action": "Allow",
        "terminate_session": False,
        "reason_codes": [
            "low_risk_routine_authorized",
        ],
        "risk_score": 0.02,
    }

    def fake_enforced(resource):
        observed.append(resource)

        return (
            event,
            analysis,
            policy_result,
        )

    monkeypatch.setattr(
        resources,
        "_log_analyze_and_enforce_access",
        fake_enforced,
    )

    def forbidden_old_path(resource):
        pytest.fail(
            "_resource_response must use the unified "
            "ML + policy enforcement helper."
        )

    monkeypatch.setattr(
        resources,
        "_log_and_analyze_access",
        forbidden_old_path,
    )

    with app.app_context():
        response, status = resources._resource_response(
            "normal_page"
        )

    assert observed == [
        "normal_page"
    ]

    assert status == 200

    assert response.get_json() == {
        "title": "Normal Employee Page",
        "sensitivity": "low",
        "message": (
            "General company info, "
            "visible to all employees."
        ),
    }



def test_denied_admin_access_is_logged_and_analyzed(
    monkeypatch,
) -> None:
    app = Flask(
        "admin-analysis-trigger-test"
    )

    observed = []

    event = SimpleNamespace(
        id=99,
        session_id="session-denied-admin",
    )

    analysis = {
        "prediction": {
            "predicted_risk": "low",
            "probability_low": 0.95,
            "probability_medium": 0.03,
            "probability_high": 0.02,
        },
        "anomaly_detection": {
            "is_anomaly": False,
        },
        "behavioral_cluster": {
            "cluster_id": 1,
        },
    }

    policy_result = {
        "action": "Restrict",
        "terminate_session": False,
        "reason_codes": [
            "privilege_mismatch",
        ],
        "risk_score": 0.02,
    }

    def fake_enforced(resource):
        observed.append(resource)

        return (
            event,
            analysis,
            policy_result,
        )

    monkeypatch.setattr(
        resources,
        "_log_analyze_and_enforce_access",
        fake_enforced,
    )

    def forbidden_old_path(resource):
        pytest.fail(
            "Admin access must use the unified "
            "ML + policy enforcement helper."
        )

    monkeypatch.setattr(
        resources,
        "_log_and_analyze_access",
        forbidden_old_path,
    )

    with app.test_request_context(
        "/api/resources/admin"
    ):
        response, status = (
            resources.admin_page.__wrapped__()
        )

    assert observed == [
        "admin_page"
    ]

    assert status == 403

    assert response.get_json() == {
        "error": (
            "Access restricted by Zero Trust policy."
        ),
        "policy_action": "Restrict",
    }
