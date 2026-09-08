import json
import pytest
from app import create_app
from app.extensions import db
from app.models import User, Session
from config import Config

from app.services.policy_engine import decide_zero_trust_policy

def mock_allow_policy(*args, **kwargs):
    return {
        "action": "Allow",
        "reason_codes": ["low_risk_test"],
        "terminate_session": False
    }

def test_portal_endpoints_active_and_terminated(monkeypatch):
    monkeypatch.setattr("app.routes.resources.apply_zero_trust_policy", mock_allow_policy)
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setattr(Config, "TESTING", True, raising=False)
    monkeypatch.setattr(Config, "WTF_CSRF_ENABLED", False, raising=False)
    
    app = create_app()
    client = app.test_client()

    with app.app_context():
        db.create_all()
        user = User(username="employee1", email="employee1@test.com", role="employee")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

        # Login
        resp = client.post("/api/auth/login", json={"username": "employee1", "password": "password"})
        assert resp.status_code == 200
        
        # 1. Test Active session -> Tasks works
        resp = client.get("/api/resources/tasks")
        assert resp.status_code == 200
        assert resp.json["title"] == "My Tasks"

        # 2. Test Active session -> Policies works
        resp = client.get("/api/resources/policies")
        assert resp.status_code == 200
        assert resp.json["title"] == "Company Policies"

        # 3. Test Active session -> Announcements works
        resp = client.get("/api/resources/announcements")
        assert resp.status_code == 200
        assert resp.json["title"] == "Announcements"

        # Terminate the session
        session_row = Session.query.filter_by(user_id=user.id).first()
        session_row.is_active = False
        db.session.commit()

        # 4. Click Tasks -> protected content must not appear (returns 401)
        resp = client.get("/api/resources/tasks")
        assert resp.status_code == 401
        assert "terminated" in resp.json["error"]

        # 5. Click Policies -> protected content must not appear
        resp = client.get("/api/resources/policies")
        assert resp.status_code == 401
        assert "terminated" in resp.json["error"]

        # 6. Click Announcements -> protected content must not appear
        resp = client.get("/api/resources/announcements")
        assert resp.status_code == 401
        assert "terminated" in resp.json["error"]

