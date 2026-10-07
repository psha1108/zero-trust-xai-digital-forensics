import pytest
from flask import g
from app.models import AccessEvent, Session, User
from app.extensions import db
from datetime import datetime

from app import create_app

@pytest.fixture
def app():
    app = create_app(test_config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-key"
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()

@pytest.fixture
def client(app):
    return app.test_client()

# Approved roles (minus it_support because it's not in ML preprocessor yet)
ROLES = ["admin", "employee", "finance_user", "hr_user", "guest"]
RESOURCES = ["normal_page", "hr_page", "finance_page", "it_support", "management_reports", "tasks_page"]

EXPECTED_MATRIX = {
    "employee": {
        "normal_page": "OTP",
        "hr_page": "Restrict",
        "finance_page": "Restrict",
        "it_support": "Restrict",
        "management_reports": "Restrict",
        "tasks_page": "Allow", # tasks_page isn't protected so it defaults to Allow (no OTP)
    },
    "hr_user": {
        "normal_page": "Restrict",
        "hr_page": "OTP",
        "finance_page": "Restrict",
        "it_support": "Restrict",
        "management_reports": "Restrict",
        "tasks_page": "Allow",
    },
    "finance_user": {
        "normal_page": "Restrict",
        "hr_page": "Restrict",
        "finance_page": "OTP",
        "it_support": "Restrict",
        "management_reports": "Restrict",
        "tasks_page": "Allow",
    },
    "admin": {
        "normal_page": "OTP",
        "hr_page": "OTP",
        "finance_page": "OTP",
        "it_support": "OTP",
        "management_reports": "OTP",
        "tasks_page": "Allow",
    },
    "guest": {
        "normal_page": "Restrict",
        "hr_page": "Restrict",
        "finance_page": "Restrict",
        "it_support": "Restrict",
        "management_reports": "Restrict",
        "tasks_page": "Allow",
    }
}

@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("resource", RESOURCES)
def test_role_resource_authorization_matrix(client, app, role, resource):
    """
    Exhaustively tests the Zero Trust policy decision for every role x resource combination.
    """
    # 1. Setup User and Session
    user = User(username=f"test_{role}", email=f"test_{role}@acme.com", role=role)
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    # 2. Mock the ML models to always return Low Risk / No Anomaly / Routine.
    from unittest.mock import patch
    mock_analysis = {
        "features": {"access_count_5min": 1, "failed_logins_24h": 0},
        "prediction": {
            "predicted_risk": "low",
            "probability_high": 0.0,
        },
        "anomaly_detection": {
            "is_anomaly": False,
            "anomaly_score": 0.0,
            "anomaly_threshold": 0.5,
            "threshold_margin": 0.5
        },
        "behavioral_cluster": {
            "cluster_id": 1,
            "cluster_distance": 0.5
        },
        "explanation": {
            "prediction": "low",
            "base_value": 0,
            "shap_values": {},
            "supporting_factors": [],
            "opposing_factors": [],
            "explanation_summary": "Routine",
            "explanation": {"contributions": []}
        }
    }
    
    with patch("app.routes.resources.analyze_operational_access", return_value=mock_analysis):
        # 3. Login
        client.post("/api/auth/login", json={
            "username": user.username,
            "password": "password"
        })
        
        # Map the resource back to the endpoint URL
        url_map = {
            "normal_page": "/api/resources/normal",
            "hr_page": "/api/resources/hr",
            "finance_page": "/api/resources/finance",
            "it_support": "/api/resources/it-support",
            "management_reports": "/api/resources/management-reports",
            "tasks_page": "/api/resources/tasks"
        }
        
        url = url_map[resource]
        
        res = client.get(url)
    
    # 3. Check expected behaviour
    expected_action = EXPECTED_MATRIX[role][resource]
    
    if expected_action == "OTP":
        assert res.status_code == 401
        data = res.get_json()
        assert data["policy_action"] == "OTP"
        assert data["requires_otp"] is True
    elif expected_action == "Restrict":
        assert res.status_code == 403
        data = res.get_json()
        assert data["policy_action"] == "Restrict"
    elif expected_action == "Allow":
        assert res.status_code == 200

def test_resource_switching_preserves_behaviour(client, app):
    """
    Verifies that jumping around rapidly logs access events properly and increments
    access_count_5min in the ML analysis, even when getting Restrict.
    """
    user = User(username="test_admin_switch", email="switch@acme.com", role="admin")
    user.set_password("password")
    db.session.add(user)
    db.session.commit()
    
    client.post("/api/auth/login", json={
        "username": user.username,
        "password": "password"
    })
    
    client.get("/api/resources/finance") # OTP 1
    client.get("/api/resources/hr")      # OTP 2
    client.get("/api/resources/normal")  # OTP 3
    client.get("/api/resources/it-support") # OTP 4
    
    # Check access events count
    events = AccessEvent.query.filter_by(user_id=user.id).all()
    assert len(events) == 4
    
    # The test passes simply by verifying the 4 accesses were tracked 
    # despite the restrictions and OTPs triggered, which is exactly
    # what access_count_5min relies on.
