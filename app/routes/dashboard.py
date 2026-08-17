from flask import Blueprint, jsonify, session as flask_session
from flask_login import login_required, current_user
from app.models import Session, LoginEvent, AccessEvent

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/session-status", methods=["GET"])
@login_required
def session_status():
    app_session_id = flask_session.get("app_session_id")
    session_row = Session.query.filter_by(session_id=app_session_id).first()
    
    if not session_row:
        return jsonify({"error": "No active session found"}), 404
        
    return jsonify({
        "username": current_user.username,
        "role": current_user.role,
        "session_id": session_row.session_id,
        "started_at": session_row.started_at.isoformat() if session_row.started_at else None,
        "current_ip": session_row.current_ip,
        "current_device_fingerprint": session_row.current_device_fingerprint,
        "is_active": session_row.is_active
    }), 200


@dashboard_bp.route("/login-history", methods=["GET"])
@login_required
def login_history():
    events = LoginEvent.query.filter_by(user_id=current_user.id)\
                             .order_by(LoginEvent.timestamp.desc())\
                             .limit(10).all()
    
    result = []
    for event in events:
        result.append({
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "username": event.username_attempted,
            "status": "Success" if event.success else "Failed",
            "ip_address": event.ip_address,
            "device": event.device_info or "Unknown"
        })
        
    return jsonify(result), 200


@dashboard_bp.route("/access-history", methods=["GET"])
@login_required
def access_history():
    events = AccessEvent.query.filter_by(user_id=current_user.id)\
                              .order_by(AccessEvent.timestamp.desc())\
                              .limit(10).all()
                              
    result = []
    for event in events:
        result.append({
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "resource": event.resource,
            "sensitivity": event.resource_sensitivity,
            "ip_address": event.ip_address,
            "device_changed": event.device_changed,
            "ip_changed": event.ip_changed
        })
        
    return jsonify(result), 200