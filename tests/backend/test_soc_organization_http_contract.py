"""HTTP contract for organization-wide SOC dashboard endpoints.

The tests use the real Flask routes and an isolated SQLite database.

They freeze:
- explicit admin-only access to every /soc endpoint,
- organization-wide visibility for an authenticated admin,
- cross-user session/login/access projections,
- persisted Security State projection,
- persisted Zero Trust alert mapping.

The SOC routes are read-only views of already persisted state.
"""

from __future__ import annotations

from datetime import datetime

from app import create_app
from app.extensions import db
from app.models import (
    AccessEvent,
    LoginEvent,
    Session,
    User,
)
from config import Config


SOC_ENDPOINTS = (
    "/api/dashboard/soc/active-sessions",
    "/api/dashboard/soc/login-history",
    "/api/dashboard/soc/access-history",
    "/api/dashboard/soc/security-state",
    "/api/dashboard/soc/security-alerts",
)

PASSWORD = "StrongPass1!"


def _build_app(monkeypatch):
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
        "soc-http-contract-test-key",
    )

    app = create_app()

    with app.app_context():
        db.create_all()

        admin = User(
            username="socadmin",
            email="socadmin@example.test",
            role="admin",
        )

        employee = User(
            username="socemployee",
            email="socemployee@example.test",
            role="employee",
        )

        admin.set_password(
            PASSWORD
        )

        employee.set_password(
            PASSWORD
        )

        db.session.add_all(
            (
                admin,
                employee,
            )
        )

        db.session.commit()

        admin_id = admin.id
        employee_id = employee.id

    return (
        app,
        admin_id,
        employee_id,
    )


def _login(
    client,
    *,
    username,
):
    response = client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": PASSWORD,
        },
        headers={
            "User-Agent":
                "SOCContractBrowser/1.0",
        },
    )

    assert response.status_code == 200

    with client.session_transaction() as flask_session:
        session_id = flask_session[
            "app_session_id"
        ]

    return session_id


def _seed_employee_incident(
    app,
    *,
    employee_id,
    session_id,
):
    with app.app_context():
        login_event = (
            LoginEvent.query
            .filter_by(
                user_id=employee_id,
                success=True,
            )
            .one()
        )

        login_event.risk_label = "low"
        login_event.anomaly_score = 0.645953
        login_event.cluster_id = 1
        login_event.action_taken = "Restrict"

        session_row = (
            Session.query
            .filter_by(
                session_id=session_id,
                user_id=employee_id,
            )
            .one()
        )

        session_row.current_risk_label = "low"
        session_row.current_risk_score = 0.02

        incident_time = datetime(
            2026,
            9,
            3,
            22,
            45,
            16,
        )

        event = AccessEvent(
            user_id=employee_id,
            session_id=session_id,
            resource="management_reports",
            resource_sensitivity="high",
            timestamp=incident_time,
            request_count=1,
            ip_address="127.0.0.1",
            device_id="soc-contract-device",
            device_fingerprint="soc-contract-fingerprint",
            privilege_mismatch=True,
            ip_changed=False,
            device_changed=False,
            decision="Restrict",
            risk_score=0.02,
        )

        db.session.add(
            event
        )

        db.session.commit()

        event_id = event.id

    return (
        event_id,
        incident_time,
    )


def _cleanup(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_soc_routes_reject_unauthenticated_requests(
    monkeypatch,
):
    (
        app,
        _,
        _,
    ) = _build_app(
        monkeypatch
    )

    client = app.test_client()

    try:
        for endpoint in SOC_ENDPOINTS:
            response = client.get(
                endpoint
            )

            # The application authentication boundary executes
            # before the SOC-specific admin-role guard.
            assert response.status_code == 401

    finally:
        _cleanup(
            app
        )


def test_soc_routes_reject_authenticated_non_admin(
    monkeypatch,
):
    (
        app,
        _,
        _,
    ) = _build_app(
        monkeypatch
    )

    employee_client = app.test_client()

    try:
        _login(
            employee_client,
            username="socemployee",
        )

        for endpoint in SOC_ENDPOINTS:
            response = employee_client.get(
                endpoint
            )

            assert response.status_code == 403

            assert response.get_json() == {
                "error":
                    "Forbidden - admin role required."
            }

    finally:
        _cleanup(
            app
        )


def test_admin_sees_cross_user_persisted_soc_state(
    monkeypatch,
):
    (
        app,
        _,
        employee_id,
    ) = _build_app(
        monkeypatch
    )

    employee_client = app.test_client()
    admin_client = app.test_client()

    try:
        employee_session_id = _login(
            employee_client,
            username="socemployee",
        )

        (
            incident_event_id,
            incident_time,
        ) = _seed_employee_incident(
            app,
            employee_id=employee_id,
            session_id=employee_session_id,
        )

        admin_session_id = _login(
            admin_client,
            username="socadmin",
        )

        # ------------------------------------------
        # Organization-wide active sessions
        # ------------------------------------------

        response = admin_client.get(
            "/api/dashboard/soc/active-sessions"
        )

        assert response.status_code == 200

        active_sessions = response.get_json()

        assert any(
            row[
                "session_id"
            ] == employee_session_id
            and row[
                "user_id"
            ] == employee_id
            and row[
                "username"
            ] == "socemployee"
            and row[
                "risk_label"
            ] == "low"
            and row[
                "risk_score"
            ] == 0.02
            and row[
                "is_active"
            ] is True
            for row in active_sessions
        )

        assert any(
            row[
                "session_id"
            ] == admin_session_id
            and row[
                "username"
            ] == "socadmin"
            for row in active_sessions
        )

        # ------------------------------------------
        # Organization-wide login history
        # ------------------------------------------

        response = admin_client.get(
            "/api/dashboard/soc/login-history"
        )

        assert response.status_code == 200

        login_history = response.get_json()

        employee_logins = [
            row
            for row in login_history
            if (
                row["user_id"] == employee_id
                and row["success"] is True
            )
        ]

        assert len(
            employee_logins
        ) == 1

        employee_login = employee_logins[0]

        assert employee_login[
            "username"
        ] == "socemployee"

        assert employee_login[
            "session_id"
        ] == employee_session_id

        assert employee_login[
            "risk_label"
        ] == "low"

        assert employee_login[
            "anomaly_score"
        ] == 0.645953

        assert employee_login[
            "cluster_id"
        ] == 1

        assert employee_login[
            "action_taken"
        ] == "Restrict"

        # ------------------------------------------
        # Organization-wide access history
        # ------------------------------------------

        response = admin_client.get(
            "/api/dashboard/soc/access-history"
        )

        assert response.status_code == 200

        access_history = response.get_json()

        assert access_history == [
            {
                "event_id":
                    incident_event_id,

                "timestamp":
                    incident_time.isoformat(),

                "user_id":
                    employee_id,

                "username":
                    "socemployee",

                "session_id":
                    employee_session_id,

                "resource":
                    "management_reports",

                "decision":
                    "Restrict",

                "risk_score":
                    0.02,

                "privilege_mismatch":
                    True,

                "ip_address":
                    "127.0.0.1",

                "device_id":
                    "soc-contract-device",
            }
        ]

        # ------------------------------------------
        # Latest organization-wide security state
        # ------------------------------------------

        response = admin_client.get(
            "/api/dashboard/soc/security-state"
        )

        assert response.status_code == 200

        assert response.get_json() == {
            "session_id":
                employee_session_id,

            "user_id":
                employee_id,

            "username":
                "socemployee",

            "risk_label":
                "low",

            "risk_score":
                0.02,

            "anomaly_score":
                0.645953,

            "cluster_id":
                1,

            "latest_action":
                "Restrict",

            "latest_resource":
                "management_reports",

            "latest_access_at":
                incident_time.isoformat(),

            "privilege_mismatch":
                True,

            "is_active":
                True,

            "has_analysis":
                True,
        }

        # ------------------------------------------
        # Organization-wide alert mapping
        # ------------------------------------------

        response = admin_client.get(
            "/api/dashboard/soc/security-alerts"
        )

        assert response.status_code == 200

        assert response.get_json() == [
            {
                "event_id":
                    incident_event_id,

                "timestamp":
                    incident_time.isoformat(),

                "severity":
                    "high",

                "alert_type":
                    "ACCESS_RESTRICTED",

                "message":
                    "Resource access restricted by Zero Trust policy.",

                "resource":
                    "management_reports",

                "policy_action":
                    "Restrict",

                "risk_score":
                    0.02,

                "privilege_mismatch":
                    True,

                "session_id":
                    employee_session_id,

                "user_id":
                    employee_id,

                "username":
                    "socemployee",

                "evidence_data":
                    None,
            }
        ]

    finally:
        _cleanup(
            app
        )
