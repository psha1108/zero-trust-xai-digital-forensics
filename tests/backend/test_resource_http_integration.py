"""Authenticated Flask -> AccessEvent -> RF -> SHAP integration test."""

from __future__ import annotations

import json

from app import create_app
from app.extensions import db
from app.models import AccessEvent, LoginEvent, Session, User
from app.routes import resources
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
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        user_id = user.id

    real_analyze = resources.analyze_operational_access

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

    login_payload = login_response.get_json()

    assert login_payload["message"] == "Login successful."
    assert login_payload["user"]["id"] == user_id
    assert login_payload["user"]["username"] == username
    assert login_payload["user"]["role"] == "employee"

    with client.session_transaction() as flask_session:
        session_id = flask_session["app_session_id"]

    finance_response = client.get(
        "/api/resources/finance",
        headers={
            "User-Agent": user_agent,
        },
    )

    assert finance_response.status_code == 200

    assert finance_response.get_json() == {
        "title": "Finance Page",
        "sensitivity": "high",
        "message": "Sensitive financial records.",
    }

    assert observed["calls"] == 1
    assert observed["session_id"] == session_id
    assert observed["analysis"] is not None

    analysis = observed["analysis"]

    assert analysis["prediction"]["predicted_risk"] in {
        "low",
        "medium",
        "high",
    }

    assert (
        analysis["prediction"]["predicted_risk"]
        == analysis["explanation"]["prediction"]
    )

    assert analysis["explanation"]["class_order"] == [
        "high",
        "low",
        "medium",
    ]

    assert (
        analysis["explanation"]["additivity"]["is_additive"]
        is True
    )

    json.dumps(analysis)

    with app.app_context():
        login_events = (
            LoginEvent.query
            .filter_by(user_id=user_id)
            .order_by(LoginEvent.id.asc())
            .all()
        )

        assert len(login_events) == 1
        assert login_events[0].success is True
        assert login_events[0].session_id == session_id

        session_row = Session.query.filter_by(
            session_id=session_id
        ).one()

        assert session_row.user_id == user_id
        assert session_row.is_active is True

        access_events = (
            AccessEvent.query
            .filter_by(
                user_id=user_id,
                session_id=session_id,
            )
            .order_by(AccessEvent.id.asc())
            .all()
        )

        assert len(access_events) == 1

        event = access_events[0]

        assert event.id == observed["access_event_id"]
        assert event.resource == "finance_page"
        assert event.resource_sensitivity == "high"
        assert event.privilege_mismatch is False
        assert event.ip_changed is False
        assert event.device_changed is False

        # Policy enforcement remains intentionally outside Stage C.
        assert event.decision is None
        assert event.risk_score is None

        db.session.remove()
        db.drop_all()