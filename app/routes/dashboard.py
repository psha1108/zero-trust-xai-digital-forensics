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


@dashboard_bp.route("/security-state", methods=["GET"])
@login_required
def security_state():
    """Return persisted security state for the current session only."""

    app_session_id = flask_session.get("app_session_id")

    session_row = (
        Session.query
        .filter_by(
            session_id=app_session_id,
            user_id=current_user.id,
        )
        .first()
    )

    if not session_row:
        return jsonify({
            "error": "No active session found"
        }), 404

    login_event = session_row.login_event

    latest_access = (
        AccessEvent.query
        .filter_by(
            session_id=session_row.session_id,
            user_id=current_user.id,
        )
        .order_by(
            AccessEvent.timestamp.desc()
        )
        .first()
    )

    anomaly_score = (
        login_event.anomaly_score
        if login_event
        else None
    )

    cluster_id = (
        login_event.cluster_id
        if login_event
        else None
    )

    login_risk_label = (
        login_event.risk_label
        if login_event
        else None
    )

    risk_label = session_row.current_risk_label
    risk_score = session_row.current_risk_score

    has_analysis = (
        risk_label is not None
        and risk_score is not None
        and anomaly_score is not None
        and cluster_id is not None
        and login_risk_label is not None
    )

    return jsonify({
        "session_id": session_row.session_id,
        "risk_label": risk_label,
        "risk_score": risk_score,
        "anomaly_score": anomaly_score,
        "cluster_id": cluster_id,
        "latest_action": (
            latest_access.decision
            if latest_access
            else None
        ),
        "latest_resource": (
            latest_access.resource
            if latest_access
            else None
        ),
        "latest_access_at": (
            latest_access.timestamp.isoformat()
            if (
                latest_access
                and latest_access.timestamp
            )
            else None
        ),
        "privilege_mismatch": (
            latest_access.privilege_mismatch
            if latest_access
            else None
        ),
        "is_active": session_row.is_active,
        "has_analysis": has_analysis,
    }), 200

@dashboard_bp.route("/security-alerts", methods=["GET"])
@login_required
def security_alerts():
    """Return persisted Zero Trust security alerts for the current user.

    This endpoint is a read-only projection of existing AccessEvent rows.
    It does not execute ML models, SHAP, or the Zero Trust policy engine.
    """

    events = (
        AccessEvent.query
        .filter_by(
            user_id=current_user.id,
        )
        .filter(
            (
                AccessEvent.decision.in_(
                    (
                        "OTP",
                        "Restrict",
                        "Block",
                    )
                )
            )
            | (
                AccessEvent.privilege_mismatch.is_(True)
            )
        )
        .order_by(
            AccessEvent.timestamp.desc()
        )
        .limit(20)
        .all()
    )

    alerts = []

    for event in events:
        decision = event.decision

        if decision == "Block":
            severity = "critical"
            alert_type = "SESSION_BLOCKED"
            message = (
                "Session blocked by Zero Trust policy."
            )

        elif decision == "Restrict":
            severity = "high"
            alert_type = "ACCESS_RESTRICTED"
            message = (
                "Access restricted by Zero Trust policy."
            )

        elif event.privilege_mismatch:
            severity = "high"
            alert_type = "PRIVILEGE_MISMATCH"
            message = (
                "Privilege mismatch detected for requested resource."
            )

        elif decision == "OTP":
            severity = "medium"
            alert_type = "OTP_REQUIRED"
            message = (
                "OTP verification required by Zero Trust policy."
            )

        else:
            continue

        alerts.append({
            "event_id": event.id,
            "timestamp": (
                event.timestamp.isoformat()
                if event.timestamp
                else None
            ),
            "severity": severity,
            "alert_type": alert_type,
            "message": message,
            "resource": event.resource,
            "policy_action": event.decision,
            "risk_score": event.risk_score,
            "privilege_mismatch": event.privilege_mismatch,
            "session_id": event.session_id,
        })

    return jsonify(alerts), 200
