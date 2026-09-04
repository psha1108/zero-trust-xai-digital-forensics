"""Authenticated Flask -> ML -> Zero Trust HTTP integration test."""

from __future__ import annotations

import json

import pytest

from app import create_app
from app.extensions import db
from app.models import AccessEvent, LoginEvent, Session, User
from app.routes import resources
from app.services.policy_engine import decide_zero_trust_policy
from config import Config


def test_authenticated_resource_request_runs_real_rf_and_shap(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        Config,
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:///:memory:",
    )

    monkeypatch.setattr(
        Config,
        "TESTING",
        True,
        raising=False,
    )

    monkeypatch.setattr(
        Config,
        "SECRET_KEY",
        "backend-http-integration-test-key",
    )

    app = create_app()

    username = "httpuser"
    password = "StrongPass1!"

    with app.app_context():
        db.create_all()

        user = User(
            username=username,
            email="httpuser@example.com",
            role="employee",
        )

        user.set_password(
            password
        )

        db.session.add(user)
        db.session.commit()

        user_id = user.id

    real_analyze = (
        resources.analyze_operational_access
    )

    observed = {
        "calls": 0,
        "session_id": None,
        "access_event_id": None,
        "analysis": None,
    }

    def recording_analyze(
        *,
        session_id,
        access_event_id,
    ):
        result = real_analyze(
            session_id=session_id,
            access_event_id=access_event_id,
        )

        observed["calls"] += 1
        observed["session_id"] = session_id
        observed["access_event_id"] = access_event_id
        observed["analysis"] = result

        return result

    monkeypatch.setattr(
        resources,
        "analyze_operational_access",
        recording_analyze,
    )

    client = app.test_client()

    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": password,
        },
        headers={
            "User-Agent": user_agent,
        },
    )

    assert login_response.status_code == 200

    login_payload = (
        login_response.get_json()
    )

    assert login_payload["message"] == (
        "Login successful."
    )

    assert login_payload["user"]["id"] == user_id
    assert login_payload["user"]["username"] == username
    assert login_payload["user"]["role"] == "employee"

    with client.session_transaction() as flask_session:
        session_id = flask_session[
            "app_session_id"
        ]

    finance_response = client.get(
        "/api/resources/finance",
        headers={
            "User-Agent": user_agent,
        },
    )

    assert observed["calls"] == 1
    assert observed["session_id"] == session_id
    assert observed["analysis"] is not None

    analysis = observed[
        "analysis"
    ]

    anomaly_detection = analysis[
        "anomaly_detection"
    ]

    assert set(anomaly_detection) == {
        "anomaly_score",
        "anomaly_threshold",
        "threshold_margin",
        "is_anomaly",
    }

    assert isinstance(
        anomaly_detection["anomaly_score"],
        float,
    )

    assert anomaly_detection[
        "anomaly_threshold"
    ] == pytest.approx(
        0.5532259181941123,
        abs=1e-15,
    )

    assert anomaly_detection[
        "threshold_margin"
    ] == pytest.approx(
        anomaly_detection["anomaly_score"]
        - anomaly_detection["anomaly_threshold"],
        abs=1e-12,
    )

    assert anomaly_detection[
        "is_anomaly"
    ] == (
        anomaly_detection["anomaly_score"]
        >= anomaly_detection["anomaly_threshold"]
    )

    assert set(
        analysis["behavioral_cluster"]
    ) == {
        "cluster_id",
        "archetype_name",
    }

    assert analysis[
        "behavioral_cluster"
    ]["cluster_id"] in {
        0,
        1,
    }

    expected_archetypes = {
        0: "Elevated Behavioral Activity",
        1: "Routine Behavioral Activity",
    }

    assert analysis[
        "behavioral_cluster"
    ]["archetype_name"] == (
        expected_archetypes[
            analysis[
                "behavioral_cluster"
            ]["cluster_id"]
        ]
    )

    prediction = analysis[
        "prediction"
    ]

    assert prediction[
        "predicted_risk"
    ] in {
        "low",
        "medium",
        "high",
    }

    probabilities = [
        prediction["probability_low"],
        prediction["probability_medium"],
        prediction["probability_high"],
    ]

    assert sum(
        probabilities
    ) == pytest.approx(
        1.0,
        abs=1e-12,
    )

    assert (
        prediction["predicted_risk"]
        == analysis["explanation"]["prediction"]
    )

    assert analysis[
        "explanation"
    ]["class_order"] == [
        "high",
        "low",
        "medium",
    ]

    assert (
        analysis[
            "explanation"
        ]["additivity"]["is_additive"]
        is True
    )

    json.dumps(
        analysis
    )

    expected_policy = decide_zero_trust_policy(
        analysis=analysis,
        privilege_mismatch=False,
    )

    expected_action = expected_policy[
        "action"
    ]

    if expected_action == "Allow":
        assert finance_response.status_code == 200

        assert finance_response.get_json() == {
            "title": "Finance Page",
            "sensitivity": "high",
            "message": "Sensitive financial records.",
        }

    elif expected_action == "OTP":
        assert finance_response.status_code == 401

        assert finance_response.get_json() == {
            "error": "OTP verification required.",
            "policy_action": "OTP",
            "requires_otp": True,
        }

    elif expected_action == "Restrict":
        assert finance_response.status_code == 403

        assert finance_response.get_json() == {
            "error": (
                "Access restricted by Zero Trust policy."
            ),
            "policy_action": "Restrict",
        }

    elif expected_action == "Block":
        assert finance_response.status_code == 401

        assert finance_response.get_json() == {
            "error": (
                "Session blocked by Zero Trust policy."
            ),
            "policy_action": "Block",
        }

    else:
        raise AssertionError(
            f"Unexpected policy action: {expected_action}"
        )

    with app.app_context():
        login_events = (
            LoginEvent.query
            .filter_by(
                user_id=user_id
            )
            .order_by(
                LoginEvent.id.asc()
            )
            .all()
        )

        assert len(login_events) == 1

        login_event = login_events[
            0
        ]

        assert login_event.success is True
        assert login_event.session_id == session_id

        assert login_event.anomaly_score == pytest.approx(
            anomaly_detection["anomaly_score"],
            abs=1e-15,
        )

        assert login_event.risk_label == (
            prediction["predicted_risk"]
        )

        assert login_event.cluster_id == (
            analysis[
                "behavioral_cluster"
            ]["cluster_id"]
        )

        assert login_event.action_taken == (
            expected_action
        )

        session_row = (
            Session.query
            .filter_by(
                session_id=session_id
            )
            .one()
        )

        assert session_row.user_id == user_id

        assert session_row.current_risk_label == (
            prediction["predicted_risk"]
        )

        assert session_row.current_risk_score == pytest.approx(
            prediction["probability_high"],
            abs=1e-15,
        )

        access_events = (
            AccessEvent.query
            .filter_by(
                user_id=user_id,
                session_id=session_id,
            )
            .order_by(
                AccessEvent.id.asc()
            )
            .all()
        )

        assert len(access_events) == 1

        event = access_events[
            0
        ]

        assert event.id == observed[
            "access_event_id"
        ]

        assert event.resource == (
            "finance_page"
        )

        assert event.resource_sensitivity == (
            "high"
        )

        assert event.privilege_mismatch is False
        assert event.ip_changed is False
        assert event.device_changed is False

        assert event.decision == (
            expected_action
        )

        assert event.risk_score == pytest.approx(
            prediction["probability_high"],
            abs=1e-15,
        )

        if expected_action == "Block":
            assert session_row.is_active is False
            assert session_row.ended_at is not None
            assert session_row.end_reason == "blocked"
        else:
            assert session_row.is_active is True
            assert session_row.ended_at is None
            assert session_row.end_reason is None

        db.session.remove()
        db.drop_all()
