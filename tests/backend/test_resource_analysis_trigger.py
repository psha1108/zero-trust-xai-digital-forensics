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
    app = Flask("resource-analysis-trigger-test")

    observed = []

    event = SimpleNamespace(
        id=10,
        session_id="session-normal",
    )

    analysis = {
        "prediction": {
            "predicted_risk": "low",
        },
    }

    def fake_combined(resource):
        observed.append(resource)
        return event, analysis

    monkeypatch.setattr(
        resources,
        "_log_and_analyze_access",
        fake_combined,
        raising=False,
    )

    def forbidden_old_path(resource):
        pytest.fail(
            "_resource_response must not call _log_access directly."
        )

    monkeypatch.setattr(
        resources,
        "_log_access",
        forbidden_old_path,
    )

    with app.app_context():
        response, status = resources._resource_response(
            "normal_page"
        )

        assert status == 200
        assert observed == ["normal_page"]

        assert response.get_json() == {
            "title": "Normal Employee Page",
            "sensitivity": "low",
            "message": (
                "General company info, visible to all employees."
            ),
        }


def test_denied_admin_access_is_logged_and_analyzed(
    monkeypatch,
) -> None:
    app = Flask("admin-analysis-trigger-test")

    observed = []

    monkeypatch.setattr(
        resources,
        "current_user",
        SimpleNamespace(
            role="employee",
        ),
    )

    event = SimpleNamespace(
        id=99,
        session_id="session-denied-admin",
    )

    analysis = {
        "prediction": {
            "predicted_risk": "high",
        },
    }

    def fake_combined(resource):
        observed.append(resource)
        return event, analysis

    monkeypatch.setattr(
        resources,
        "_log_and_analyze_access",
        fake_combined,
        raising=False,
    )

    def forbidden_old_path(resource):
        pytest.fail(
            "Denied admin access must not call _log_access directly."
        )

    monkeypatch.setattr(
        resources,
        "_log_access",
        forbidden_old_path,
    )

    with app.test_request_context(
        "/api/resources/admin"
    ):
        response, status = resources.admin_page.__wrapped__()

        assert status == 403
        assert observed == ["admin_page"]

        assert response.get_json() == {
            "error": "Forbidden — admin role required."
        }