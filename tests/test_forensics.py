import pytest
import json
import hashlib
from datetime import datetime
from flask import Blueprint
from flask_login import login_user
from app import create_app
from app.extensions import db
from app.models import User, LoginEvent, EvidenceLog, Session, AccessEvent
from app.utils.forensics_utils import preserve_evidence, verify_evidence_chain

test_bp = Blueprint("test_bp", __name__)
@test_bp.route("/force_login/<int:user_id>/<session_id>")
def force_login(user_id, session_id):
    user = User.query.get(user_id)
    login_user(user)
    from flask import session
    session["app_session_id"] = session_id
    return "OK"

@pytest.fixture
def app():
    app = create_app(test_config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-key"
    })
    app.register_blueprint(test_bp)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_user(app):
    user = User(username="admin_test", email="admin@test.com", role="admin")
    user.set_password("password")
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def normal_user(app):
    user = User(username="user_test", email="user@test.com", role="user")
    user.set_password("password")
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def mock_login_event(app, admin_user):
    event = LoginEvent(
        user_id=admin_user.id,
        username_attempted="admin_test",
        timestamp=datetime.utcnow(),
        ip_address="127.0.0.1",
        device_info="test-browser",
        success=True
    )
    db.session.add(event)
    db.session.commit()
    return event

# --- STAGE 1: EVIDENCE PRESERVATION TESTS ---

def test_preserve_evidence_first_record(app, mock_login_event):
    details = {"event": "test"}
    preserve_evidence(mock_login_event.id, details)
    db.session.commit()
    
    log = EvidenceLog.query.first()
    assert log is not None
    assert log.login_event_id == mock_login_event.id
    assert json.loads(log.details) == details
    assert log.previous_hash is None
    
    expected_str = json.dumps(details, sort_keys=True)
    expected_hash = hashlib.sha256(expected_str.encode("utf-8")).hexdigest()
    assert log.record_hash == expected_hash

def test_preserve_evidence_chain_linking(app, mock_login_event):
    preserve_evidence(mock_login_event.id, {"event": 1})
    db.session.commit()
    preserve_evidence(mock_login_event.id, {"event": 2})
    db.session.commit()
    preserve_evidence(mock_login_event.id, {"event": 3})
    db.session.commit()
    
    logs = EvidenceLog.query.order_by(EvidenceLog.id.asc()).all()
    assert len(logs) == 3
    assert logs[0].previous_hash is None
    assert logs[1].previous_hash == logs[0].record_hash
    assert logs[2].previous_hash == logs[1].record_hash

# --- STAGE 2: HASH-CHAIN INTEGRITY TESTS ---

def test_verify_evidence_chain_valid(app, mock_login_event):
    preserve_evidence(mock_login_event.id, {"event": 1})
    preserve_evidence(mock_login_event.id, {"event": 2})
    db.session.commit()
    
    result = verify_evidence_chain()
    assert result["status"] == "VALID"

def test_verify_evidence_chain_tampered_details(app, mock_login_event):
    preserve_evidence(mock_login_event.id, {"event": 1})
    preserve_evidence(mock_login_event.id, {"event": 2})
    db.session.commit()
    
    log = EvidenceLog.query.order_by(EvidenceLog.id.desc()).first()
    log.details = json.dumps({"event": "HACKED"})
    db.session.commit()
    
    result = verify_evidence_chain()
    assert result["status"] == "TAMPER DETECTED"
    assert result["affected_id"] == log.id

def test_verify_evidence_chain_tampered_record_hash(app, mock_login_event):
    preserve_evidence(mock_login_event.id, {"event": 1})
    preserve_evidence(mock_login_event.id, {"event": 2})
    db.session.commit()
    
    log = EvidenceLog.query.order_by(EvidenceLog.id.desc()).first()
    log.record_hash = "00000000000000000000"
    db.session.commit()
    
    result = verify_evidence_chain()
    assert result["status"] == "TAMPER DETECTED"

def test_verify_evidence_chain_tampered_previous_hash(app, mock_login_event):
    preserve_evidence(mock_login_event.id, {"event": 1})
    preserve_evidence(mock_login_event.id, {"event": 2})
    db.session.commit()
    
    log = EvidenceLog.query.order_by(EvidenceLog.id.desc()).first()
    log.previous_hash = "00000000000000000000"
    db.session.commit()
    
    result = verify_evidence_chain()
    assert result["status"] == "TAMPER DETECTED"

def test_verify_evidence_chain_empty(app):
    result = verify_evidence_chain()
    assert result["status"] == "VALID"

# --- STAGE 3: EVENT INTEGRATION / TRANSACTION TESTS ---

def test_auth_login_event_integration(app, admin_user):
    from app.routes.auth import _log_login_event
    from flask import request
    
    with app.test_request_context():
        event = _log_login_event("test_user", True, admin_user.id)
        
    assert event.id is not None
    log = EvidenceLog.query.first()
    assert log is not None
    assert log.login_event_id == event.id
    details = json.loads(log.details)
    assert details.get("event_type") == "LoginEvent" or details.get("event", {}).get("event_type") == "LoginEvent"

def test_resources_access_event_integration(app, admin_user, mock_login_event):
    from app.routes.resources import _log_analyze_and_enforce_access
    from flask import request, session as flask_session
    from flask_login import login_user
    
    test_session_id = "test-session-123"
    sess = Session(
        session_id=test_session_id,
        user_id=admin_user.id,
        login_event_id=mock_login_event.id,
        start_ip="127.0.0.1",
        current_ip="127.0.0.1",
        start_device_fingerprint="fp",
        current_device_fingerprint="fp"
    )
    db.session.add(sess)
    db.session.commit()
    
    with app.test_request_context():
        login_user(admin_user)
        flask_session["app_session_id"] = test_session_id
        policy_result, event_response, http_status = _log_analyze_and_enforce_access("admin_page")
        
    # We can retrieve the event from the database via the session
    from app.models import AccessEvent
    event = AccessEvent.query.filter_by(session_id=test_session_id).first()
    assert event.id is not None
    log = EvidenceLog.query.filter_by(login_event_id=mock_login_event.id).first()
    assert log is not None
    details = json.loads(log.details)
    assert details.get("event_type") == "AccessEvent" or details.get("event", {}).get("event_type") == "AccessEvent"
    assert details.get("resource") == "admin_page" or details.get("resource", {}).get("name") == "admin_page"

def test_transaction_rollback_isolation(app, mock_login_event):
    try:
        preserve_evidence(mock_login_event.id, {"event": 1})
        db.session.rollback()
    except:
        pass
    assert EvidenceLog.query.count() == 0

# --- STAGE 4 & 5: FORENSIC API & AUTHORIZATION TESTS ---

def setup_mock_data(app, user):
    login_event = LoginEvent(
        user_id=user.id,
        username_attempted=user.username,
        ip_address="1.1.1.1",
        success=True
    )
    db.session.add(login_event)
    db.session.commit()
    
    sess = Session(
        session_id="api-test-session",
        user_id=user.id,
        login_event_id=login_event.id,
        start_ip="1.1.1.1",
        current_ip="1.1.1.1",
        start_device_fingerprint="fp",
        current_device_fingerprint="fp",
        started_at=datetime.utcnow()
    )
    db.session.add(sess)
    db.session.commit()
    
    preserve_evidence(login_event.id, {"event_type": "LoginEvent"})
    db.session.commit()
    return "api-test-session"

def test_auth_unauthenticated(client):
    res = client.get("/api/forensics/evidence")
    assert res.status_code == 401

def test_auth_normal_user_forbidden(client, normal_user, app):
    sid = setup_mock_data(app, normal_user)
    client.get(f"/force_login/{normal_user.id}/{sid}")
    res = client.get("/api/forensics/evidence")
    assert res.status_code == 403

def test_api_evidence_admin(client, admin_user, app):
    sid = setup_mock_data(app, admin_user)
    client.get(f"/force_login/{admin_user.id}/{sid}")
    
    res = client.get("/api/forensics/evidence")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) > 0
    assert "record_hash" in data[0]
    assert data[0]["details"]["event_type"] == "LoginEvent"

def test_api_verify_admin(client, admin_user, app):
    sid = setup_mock_data(app, admin_user)
    client.get(f"/force_login/{admin_user.id}/{sid}")
    
    res = client.get("/api/forensics/verify")
    assert res.status_code == 200
    assert res.get_json()["status"] == "VALID"

def test_api_timeline_admin(client, admin_user, app):
    sid = setup_mock_data(app, admin_user)
    client.get(f"/force_login/{admin_user.id}/{sid}")
    
    acc = AccessEvent(user_id=admin_user.id, session_id=sid, resource="test", resource_sensitivity="low", ip_address="1.1.1.1", decision="Allow")
    db.session.add(acc)
    db.session.commit()
    
    res = client.get(f"/api/forensics/timeline/{sid}")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 2
    assert data[0]["event_type"] == "LoginEvent"
    assert data[1]["event_type"] == "AccessEvent"

def test_api_report_admin(client, admin_user, app):
    sid = setup_mock_data(app, admin_user)
    client.get(f"/force_login/{admin_user.id}/{sid}")
    
    res = client.get(f"/api/forensics/report/{sid}")
    assert res.status_code == 200
    data = res.get_json()
    assert "report_identification" in data
    assert "incident_overview" in data
    assert "evidence_inventory" in data
    assert "incident_timeline" in data
    assert "investigation_findings" in data
    assert len(data["evidence_inventory"]) > 0

# --- STAGE 6: ML / SHAP FORWARD COMPATIBILITY ---

def test_ml_compatibility_absent_fields(client, admin_user, app):
    sid = setup_mock_data(app, admin_user)
    client.get(f"/force_login/{admin_user.id}/{sid}")
    
    acc = AccessEvent(user_id=admin_user.id, session_id=sid, resource="test", resource_sensitivity="low", ip_address="1.1.1.1", decision="Allow", risk_score=None)
    db.session.add(acc)
    db.session.commit()
    
    res = client.get(f"/api/forensics/timeline/{sid}")
    assert res.status_code == 200
    data = res.get_json()
    assert data[1]["risk_score"] is None

def test_ml_compatibility_present_fields(client, admin_user, app):
    sid = setup_mock_data(app, admin_user)
    client.get(f"/force_login/{admin_user.id}/{sid}")
    
    acc = AccessEvent(user_id=admin_user.id, session_id=sid, resource="test", resource_sensitivity="low", ip_address="1.1.1.1", decision="Block", risk_score=0.99)
    db.session.add(acc)
    db.session.commit()
    
    res = client.get(f"/api/forensics/timeline/{sid}")
    assert res.status_code == 200
    data = res.get_json()
    assert data[1]["risk_score"] == 0.99
    
    rep_res = client.get(f"/api/forensics/report/{sid}")
    rep_data = rep_res.get_json()
    assert rep_data["investigation_findings"]["total_access_events"] == 1
    assert rep_data["investigation_findings"]["blocked_access_events"] == 1
