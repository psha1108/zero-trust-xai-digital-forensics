"""HTTP enforcement contract for Zero Trust policy decisions.

The ML analysis, pure policy decision, and database persistence layers
already exist independently.

This contract freezes how Flask protected-resource routes must react to
the persisted policy result:

Allow
    Return the requested resource with HTTP 200.

OTP
    Do not return the protected resource.
    Return HTTP 401 indicating step-up OTP authentication is required.
    Keep the authenticated Session active.

Restrict
    Do not return the protected resource.
    Return HTTP 403.
    Keep the authenticated Session active.

Block
    Do not return the protected resource.
    Return HTTP 401.
    Terminate the Session. Future authenticated requests using the same
    browser session must be rejected by the application session guard.

The actual OTP challenge/verification workflow is intentionally a later
step. This contract only freezes the HTTP hand-off into that workflow.
"""

from __future__ import annotations

import pytest

from app import create_app
from app.extensions import db
from app.models import AccessEvent, LoginEvent, Session, User
from app.routes import resources
from config import Config


def _analysis(
    *,
    predicted_risk: str,
    probability_low: float,
    probability_medium: float,
    probability_high: float,
    is_anomaly: bool,
    cluster_id: int,
) -> dict:
    return {
        "prediction": {
            "predicted_risk": predicted_risk,
            "probability_low": probability_low,
            "probability_medium": probability_medium,
            "probability_high": probability_high,
        },
        "anomaly_detection": {
            "anomaly_score": (
                0.60
                if is_anomaly
                else 0.40
            ),
            "anomaly_threshold": 0.5532259181941123,
            "threshold_margin": (
                0.60 - 0.5532259181941123
                if is_anomaly
                else 0.40 - 0.5532259181941123
            ),
            "is_anomaly": is_anomaly,
        },
        "behavioral_cluster": {
            "cluster_id": cluster_id,
            "archetype_name": (
                "Elevated Behavioral Activity"
                if cluster_id == 0
                else "Routine Behavioral Activity"
            ),
        },
        "explanation": {
            "prediction": predicted_risk,
        },
    }


def _authenticated_app(
    monkeypatch,
    *,
    username: str,
    analysis: dict,
):
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
        "policy-http-contract-test-key",
    )

    app = create_app()

    with app.app_context():
        db.create_all()

        user = User(
            username=username,
            email=f"{username}@example.test",
            role="employee",
        )

        user.set_password(
            "StrongPass1!"
        )

        db.session.add(user)
        db.session.commit()

        user_id = user.id

    def fake_analysis(
        *,
        session_id,
        access_event_id,
    ):
        assert isinstance(
            session_id,
            str,
        )

        assert isinstance(
            access_event_id,
            int,
        )

        return analysis

    monkeypatch.setattr(
        resources,
        "analyze_operational_access",
        fake_analysis,
    )

    client = app.test_client()

    login_response = client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": "StrongPass1!",
        },
        headers={
            "User-Agent": "PolicyContractBrowser/1.0",
        },
    )

    assert login_response.status_code == 200

    with client.session_transaction() as flask_session:
        session_id = flask_session[
            "app_session_id"
        ]

    return (
        app,
        client,
        user_id,
        session_id,
    )


def _cleanup(app) -> None:
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_allow_returns_resource_and_persists_policy(
    monkeypatch,
) -> None:
    analysis = _analysis(
        predicted_risk="low",
        probability_low=0.95,
        probability_medium=0.03,
        probability_high=0.02,
        is_anomaly=False,
        cluster_id=1,
    )

    (
        app,
        client,
        user_id,
        session_id,
    ) = _authenticated_app(
        monkeypatch,
        username="http-allow-user",
        analysis=analysis,
    )

    try:
        response = client.get(
            "/api/resources/finance",
            headers={
                "User-Agent": "PolicyContractBrowser/1.0",
            },
        )

        assert response.status_code == 200

        # Preserve the existing successful-resource API contract.
        assert response.get_json() == {
            "title": "Finance Page",
            "sensitivity": "high",
            "message": "Sensitive financial records.",
        }

        with app.app_context():
            login_event = (
                LoginEvent.query
                .filter_by(
                    user_id=user_id,
                    success=True,
                )
                .one()
            )

            access_event = (
                AccessEvent.query
                .filter_by(
                    user_id=user_id,
                    session_id=session_id,
                )
                .one()
            )

            session_row = (
                Session.query
                .filter_by(
                    session_id=session_id,
                )
                .one()
            )

            assert login_event.action_taken == "Allow"

            assert access_event.decision == "Allow"

            assert access_event.risk_score == pytest.approx(
                0.02,
                abs=1e-15,
            )

            assert session_row.current_risk_label == "low"

            assert session_row.current_risk_score == pytest.approx(
                0.02,
                abs=1e-15,
            )

            assert session_row.is_active is True

    finally:
        _cleanup(app)


def test_otp_returns_step_up_response_and_keeps_session_active(
    monkeypatch,
) -> None:
    analysis = _analysis(
        predicted_risk="medium",
        probability_low=0.10,
        probability_medium=0.70,
        probability_high=0.20,
        is_anomaly=False,
        cluster_id=1,
    )

    (
        app,
        client,
        user_id,
        session_id,
    ) = _authenticated_app(
        monkeypatch,
        username="http-otp-user",
        analysis=analysis,
    )

    try:
        response = client.get(
            "/api/resources/finance",
            headers={
                "User-Agent": "PolicyContractBrowser/1.0",
            },
        )

        assert response.status_code == 401

        assert response.get_json() == {
            "error": "OTP verification required.",
            "policy_action": "OTP",
            "requires_otp": True,
        }

        with app.app_context():
            login_event = (
                LoginEvent.query
                .filter_by(
                    user_id=user_id,
                    success=True,
                )
                .one()
            )

            access_event = (
                AccessEvent.query
                .filter_by(
                    user_id=user_id,
                    session_id=session_id,
                )
                .one()
            )

            session_row = (
                Session.query
                .filter_by(
                    session_id=session_id,
                )
                .one()
            )

            assert login_event.action_taken == "OTP"
            assert access_event.decision == "OTP"

            assert access_event.risk_score == pytest.approx(
                0.20,
                abs=1e-15,
            )

            assert session_row.current_risk_label == "medium"

            assert session_row.current_risk_score == pytest.approx(
                0.20,
                abs=1e-15,
            )

            # OTP is step-up authentication, not termination.
            assert session_row.is_active is True
            assert session_row.ended_at is None
            assert session_row.end_reason is None

    finally:
        _cleanup(app)


def test_privilege_mismatch_returns_restrict_and_keeps_session_active(
    monkeypatch,
) -> None:
    analysis = _analysis(
        predicted_risk="low",
        probability_low=0.95,
        probability_medium=0.03,
        probability_high=0.02,
        is_anomaly=False,
        cluster_id=1,
    )

    (
        app,
        client,
        user_id,
        session_id,
    ) = _authenticated_app(
        monkeypatch,
        username="http-restrict-user",
        analysis=analysis,
    )

    try:
        # Employee -> admin_page is a real persisted RBAC
        # privilege mismatch in the current resources module.
        response = client.get(
            "/api/resources/admin",
            headers={
                "User-Agent": "PolicyContractBrowser/1.0",
            },
        )

        assert response.status_code == 403

        assert response.get_json() == {
            "error": "Access restricted by Zero Trust policy.",
            "policy_action": "Restrict",
        }

        with app.app_context():
            login_event = (
                LoginEvent.query
                .filter_by(
                    user_id=user_id,
                    success=True,
                )
                .one()
            )

            access_event = (
                AccessEvent.query
                .filter_by(
                    user_id=user_id,
                    session_id=session_id,
                )
                .one()
            )

            session_row = (
                Session.query
                .filter_by(
                    session_id=session_id,
                )
                .one()
            )

            assert access_event.privilege_mismatch is True

            assert login_event.action_taken == "Restrict"
            assert access_event.decision == "Restrict"

            assert access_event.risk_score == pytest.approx(
                0.02,
                abs=1e-15,
            )

            # Restrict denies only the current access.
            assert session_row.is_active is True
            assert session_row.ended_at is None
            assert session_row.end_reason is None

    finally:
        _cleanup(app)


def test_block_returns_401_terminates_session_and_guard_rejects_next_request(
    monkeypatch,
) -> None:
    analysis = _analysis(
        predicted_risk="high",
        probability_low=0.01,
        probability_medium=0.04,
        probability_high=0.95,
        is_anomaly=True,
        cluster_id=1,
    )

    (
        app,
        client,
        user_id,
        session_id,
    ) = _authenticated_app(
        monkeypatch,
        username="http-block-user",
        analysis=analysis,
    )

    try:
        response = client.get(
            "/api/resources/finance",
            headers={
                "User-Agent": "PolicyContractBrowser/1.0",
            },
        )

        assert response.status_code == 401

        assert response.get_json() == {
            "error": "Session blocked by Zero Trust policy.",
            "policy_action": "Block",
        }

        with app.app_context():
            login_event = (
                LoginEvent.query
                .filter_by(
                    user_id=user_id,
                    success=True,
                )
                .one()
            )

            access_event = (
                AccessEvent.query
                .filter_by(
                    user_id=user_id,
                    session_id=session_id,
                )
                .one()
            )

            session_row = (
                Session.query
                .filter_by(
                    session_id=session_id,
                )
                .one()
            )

            assert login_event.action_taken == "Block"
            assert access_event.decision == "Block"

            assert access_event.risk_score == pytest.approx(
                0.95,
                abs=1e-15,
            )

            assert session_row.current_risk_label == "high"

            assert session_row.current_risk_score == pytest.approx(
                0.95,
                abs=1e-15,
            )

            assert session_row.is_active is False
            assert session_row.ended_at is not None
            assert session_row.end_reason == "blocked"

        # Flask-Login cookie may still exist, but the app-level
        # active-session guard must reject the terminated session.
        followup = client.get(
            "/api/resources/normal",
            headers={
                "User-Agent": "PolicyContractBrowser/1.0",
            },
        )

        assert followup.status_code == 401

        assert followup.get_json() == {
            "error": (
                "Session has been terminated. "
                "Please log in again."
            ),
        }

    finally:
        _cleanup(app)
