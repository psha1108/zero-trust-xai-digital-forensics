"""HTTP/runtime contract for dashboard persisted Security State.

These tests exercise the real Flask route while replacing only ORM query
objects with deterministic in-memory stubs. The endpoint must remain a
read-only projection of already-persisted Session, LoginEvent and
AccessEvent state.
"""

from datetime import datetime
from types import SimpleNamespace

from flask import Flask
from flask_login import LoginManager, UserMixin

import app.routes.dashboard as dashboard_module


ENDPOINT = "/api/dashboard/security-state"


class DummyUser(UserMixin):
    def __init__(self) -> None:
        self.id = 7
        self.username = "securitystateuser"
        self.role = "employee"

    def get_id(self) -> str:
        return str(self.id)


class QueryStub:
    def __init__(self, result) -> None:
        self.result = result
        self.filters = []
        self.order_calls = 0

    def filter_by(self, **kwargs):
        self.filters.append(
            kwargs
        )
        return self

    def order_by(self, *args):
        self.order_calls += 1
        return self

    def first(self):
        return self.result


class TimestampColumnStub:
    def desc(self):
        return "timestamp-desc"


def _build_client(
    monkeypatch,
    *,
    session_row,
    access_row,
):
    app = Flask(
        __name__
    )

    app.config.update(
        TESTING=True,
        SECRET_KEY="security-state-http-contract",
    )

    login_manager = LoginManager()
    login_manager.session_protection = None
    login_manager.init_app(
        app
    )

    user = DummyUser()

    @login_manager.user_loader
    def load_user(user_id):
        if user_id == str(user.id):
            return user

        return None

    session_query = QueryStub(
        session_row
    )

    access_query = QueryStub(
        access_row
    )

    fake_session_model = SimpleNamespace(
        query=session_query,
    )

    fake_access_model = SimpleNamespace(
        query=access_query,
        timestamp=TimestampColumnStub(),
    )

    monkeypatch.setattr(
        dashboard_module,
        "Session",
        fake_session_model,
    )

    monkeypatch.setattr(
        dashboard_module,
        "AccessEvent",
        fake_access_model,
    )

    app.register_blueprint(
        dashboard_module.dashboard_bp
    )

    client = app.test_client()

    return (
        client,
        user,
        session_query,
        access_query,
    )


def _authenticate(
    client,
    *,
    user_id: int,
    session_id: str,
) -> None:
    with client.session_transaction() as flask_session:
        flask_session["_user_id"] = str(
            user_id
        )

        flask_session["_fresh"] = True

        flask_session["app_session_id"] = (
            session_id
        )


def test_security_state_requires_authentication(
    monkeypatch,
) -> None:
    client, _, _, _ = _build_client(
        monkeypatch,
        session_row=None,
        access_row=None,
    )

    response = client.get(
        ENDPOINT
    )

    assert response.status_code == 401


def test_security_state_returns_exact_persisted_analysis(
    monkeypatch,
) -> None:
    login_event = SimpleNamespace(
        anomaly_score=0.6125,
        cluster_id=0,
        risk_label="medium",
    )

    session_row = SimpleNamespace(
        session_id="session-security-state",
        current_risk_label="medium",
        current_risk_score=0.275,
        login_event=login_event,
        is_active=True,
    )

    latest_access = SimpleNamespace(
        decision="OTP",
        resource="finance_page",
        timestamp=datetime(
            2026,
            9,
            3,
            10,
            30,
            0,
        ),
        privilege_mismatch=False,
    )

    (
        client,
        user,
        session_query,
        access_query,
    ) = _build_client(
        monkeypatch,
        session_row=session_row,
        access_row=latest_access,
    )

    _authenticate(
        client,
        user_id=user.id,
        session_id="session-security-state",
    )

    response = client.get(
        ENDPOINT
    )

    assert response.status_code == 200

    assert response.get_json() == {
        "session_id": "session-security-state",
        "risk_label": "medium",
        "risk_score": 0.275,
        "anomaly_score": 0.6125,
        "cluster_id": 0,
        "latest_action": "OTP",
        "latest_resource": "finance_page",
        "latest_access_at": "2026-09-03T10:30:00",
        "privilege_mismatch": False,
        "is_active": True,
        "has_analysis": True,
    }

    assert session_query.filters == [
        {
            "session_id": "session-security-state",
            "user_id": user.id,
        }
    ]

    assert access_query.filters == [
        {
            "session_id": "session-security-state",
            "user_id": user.id,
        }
    ]

    assert access_query.order_calls == 1


def test_security_state_returns_no_analysis_yet_without_fabrication(
    monkeypatch,
) -> None:
    login_event = SimpleNamespace(
        anomaly_score=None,
        cluster_id=None,
        risk_label=None,
    )

    session_row = SimpleNamespace(
        session_id="session-no-analysis",
        current_risk_label=None,
        current_risk_score=None,
        login_event=login_event,
        is_active=True,
    )

    (
        client,
        user,
        session_query,
        access_query,
    ) = _build_client(
        monkeypatch,
        session_row=session_row,
        access_row=None,
    )

    _authenticate(
        client,
        user_id=user.id,
        session_id="session-no-analysis",
    )

    response = client.get(
        ENDPOINT
    )

    assert response.status_code == 200

    assert response.get_json() == {
        "session_id": "session-no-analysis",
        "risk_label": None,
        "risk_score": None,
        "anomaly_score": None,
        "cluster_id": None,
        "latest_action": None,
        "latest_resource": None,
        "latest_access_at": None,
        "privilege_mismatch": None,
        "is_active": True,
        "has_analysis": False,
    }

    assert session_query.filters == [
        {
            "session_id": "session-no-analysis",
            "user_id": user.id,
        }
    ]

    assert access_query.filters == [
        {
            "session_id": "session-no-analysis",
            "user_id": user.id,
        }
    ]
