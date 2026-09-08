"""HTTP contract for the Management Reports protected resource.

Management Reports is a realistic business resource used by the final
Protected Organization Portal.

The tests freeze:
- login requirement,
- employee privilege mismatch -> Restrict,
- admin and finance_user authorization,
- high-sensitivity AccessEvent persistence.

The ML analysis is stubbed here only to make policy behavior
deterministic. Real IF/RF/K-Means/SHAP execution is covered separately
by the real end-to-end and ML integration suites.
"""

from __future__ import annotations

import pytest

from app import create_app
from app.extensions import db
from app.models import (
    AccessEvent,
    LoginEvent,
    Session,
    User,
)
from app.routes import resources
from config import Config


ENDPOINT = (
    "/api/resources/management-reports"
)

PASSWORD = "StrongPass1!"


def _analysis():
    return {
        "prediction": {
            "predicted_risk":
                "low",

            "probability_low":
                0.95,

            "probability_medium":
                0.03,

            "probability_high":
                0.02,
        },

        "anomaly_detection": {
            "anomaly_score":
                0.40,

            "anomaly_threshold":
                0.5532259181941123,

            "threshold_margin":
                0.40
                - 0.5532259181941123,

            "is_anomaly":
                False,
        },

        "behavioral_cluster": {
            "cluster_id":
                1,

            "archetype_name":
                "Routine Behavioral Activity",
        },

        "explanation": {
            "prediction":
                "low",
        },
    }


def _build_app(
    monkeypatch,
    *,
    username,
    role,
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
        "management-reports-http-contract",
    )

    app = create_app()

    with app.app_context():
        db.create_all()

        user = User(
            username=username,
            email=f"{username}@example.test",
            role=role,
        )

        user.set_password(
            PASSWORD
        )

        db.session.add(
            user
        )

        db.session.commit()

        user_id = user.id

    def deterministic_analysis(
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

        return _analysis()

    monkeypatch.setattr(
        resources,
        "analyze_operational_access",
        deterministic_analysis,
    )

    return (
        app,
        user_id,
    )


def _login(
    client,
    *,
    username,
):
    response = client.post(
        "/api/auth/login",
        json={
            "username":
                username,

            "password":
                PASSWORD,
        },
        headers={
            "User-Agent":
                "ManagementReportsContract/1.0",
        },
    )

    assert response.status_code == 200

    with client.session_transaction() as flask_session:
        session_id = flask_session[
            "app_session_id"
        ]

    return session_id


def _cleanup(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_management_reports_requires_authentication(
    monkeypatch,
):
    (
        app,
        _,
    ) = _build_app(
        monkeypatch,
        username="mgmtanonfixture",
        role="employee",
    )

    client = app.test_client()

    try:
        response = client.get(
            ENDPOINT
        )

        assert response.status_code == 401

    finally:
        _cleanup(
            app
        )


def test_employee_management_reports_privilege_mismatch_restricts(
    monkeypatch,
):
    username = "mgmtemployee"

    (
        app,
        user_id,
    ) = _build_app(
        monkeypatch,
        username=username,
        role="employee",
    )

    client = app.test_client()

    try:
        session_id = _login(
            client,
            username=username,
        )

        response = client.get(
            ENDPOINT,
            headers={
                "User-Agent":
                    "ManagementReportsContract/1.0",
            },
        )

        assert response.status_code == 403

        assert response.get_json() == {
            "error":
                "Access restricted by Zero Trust policy.",

            "policy_action":
                "Restrict",
        }

        with app.app_context():
            event = (
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

            login_event = (
                LoginEvent.query
                .filter_by(
                    user_id=user_id,
                    success=True,
                )
                .one()
            )

            assert event.resource == (
                "management_reports"
            )

            assert event.resource_sensitivity == (
                "high"
            )

            assert event.privilege_mismatch is True

            assert event.decision == (
                "Restrict"
            )

            assert event.risk_score == pytest.approx(
                0.02,
                abs=1e-15,
            )

            assert login_event.action_taken == (
                "Restrict"
            )

            assert session_row.current_risk_label == (
                "low"
            )

            assert session_row.current_risk_score == pytest.approx(
                0.02,
                abs=1e-15,
            )

            assert session_row.is_active is True
            assert session_row.ended_at is None
            assert session_row.end_reason is None

    finally:
        _cleanup(
            app
        )


@pytest.mark.parametrize(
    "role,username",
    (
        (
            "admin",
            "mgmtadmin",
        ),
        (
            "finance_user",
            "mgmtfinance",
        ),
    ),
)
def test_authorized_roles_can_access_management_reports(
    monkeypatch,
    role,
    username,
):
    (
        app,
        user_id,
    ) = _build_app(
        monkeypatch,
        username=username,
        role=role,
    )

    client = app.test_client()

    try:
        session_id = _login(
            client,
            username=username,
        )

        response = client.get(
            ENDPOINT,
            headers={
                "User-Agent":
                    "ManagementReportsContract/1.0",
            },
        )

        assert response.status_code == 200

        data = response.get_json()
        assert data["title"] == "Management Reports"
        assert data["sensitivity"] == "high"
        assert data["message"] == (
            "Internal management reports for "
            "authorized finance and administrative "
            "personnel."
        )

        with app.app_context():
            event = (
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

            assert event.resource == (
                "management_reports"
            )

            assert event.resource_sensitivity == (
                "high"
            )

            assert event.privilege_mismatch is False

            assert event.decision == (
                "Allow"
            )

            assert event.risk_score == pytest.approx(
                0.02,
                abs=1e-15,
            )

            assert session_row.is_active is True

    finally:
        _cleanup(
            app
        )
