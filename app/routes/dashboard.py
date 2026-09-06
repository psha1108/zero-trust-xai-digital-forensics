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

# === ORGANIZATION-WIDE SOC API ===
#
# These endpoints are intentionally separate from the original
# /api/dashboard/* endpoints.
#
# Original dashboard endpoints remain current-user scoped.
# /api/dashboard/soc/* is the administrator-only organization
# monitoring interface used by the Security Operations Console.


def _soc_require_admin():
    """Return a 403 response unless the authenticated user is admin."""
    if (
        not current_user.is_authenticated
        or current_user.role != "admin"
    ):
        return jsonify({
            "error": "Forbidden - admin role required."
        }), 403

    return None


def _soc_username(user_id):
    """Resolve a username without changing persistence state."""
    from app.models import User

    user = (
        User.query
        .filter_by(id=user_id)
        .first()
    )

    return (
        user.username
        if user is not None
        else "Unknown"
    )


@dashboard_bp.route(
    "/soc/active-sessions",
    methods=["GET"],
)
@login_required
def soc_active_sessions():
    """Return recent active sessions across the protected application."""
    auth_err = _soc_require_admin()

    if auth_err:
        return auth_err

    sessions = (
        Session.query
        .filter_by(is_active=True)
        .order_by(
            Session.started_at.desc(),
            Session.id.desc(),
        )
        .limit(50)
        .all()
    )

    result = []

    for row in sessions:
        result.append({
            "session_id": row.session_id,
            "user_id": row.user_id,
            "username": _soc_username(row.user_id),
            "started_at": (
                row.started_at.isoformat()
                if row.started_at
                else None
            ),
            "current_ip": row.current_ip,
            "current_device_fingerprint":
                row.current_device_fingerprint,
            "risk_label": row.current_risk_label,
            "risk_score": row.current_risk_score,
            "is_active": bool(row.is_active),
        })

    return jsonify(result), 200


@dashboard_bp.route(
    "/soc/login-history",
    methods=["GET"],
)
@login_required
def soc_login_history():
    """Return recent login events across all application users."""
    auth_err = _soc_require_admin()

    if auth_err:
        return auth_err

    events = (
        LoginEvent.query
        .order_by(
            LoginEvent.timestamp.desc(),
            LoginEvent.id.desc(),
        )
        .limit(20)
        .all()
    )

    result = []

    for event in events:
        result.append({
            "event_id": event.id,
            "timestamp": (
                event.timestamp.isoformat()
                if event.timestamp
                else None
            ),
            "user_id": event.user_id,
            "username": (
                event.username_attempted
                or (
                    _soc_username(event.user_id)
                    if event.user_id is not None
                    else "Unknown"
                )
            ),
            "success": bool(event.success),
            "ip_address": event.ip_address,
            "risk_label": event.risk_label,
            "anomaly_score": event.anomaly_score,
            "cluster_id": event.cluster_id,
            "action_taken": event.action_taken,
            "session_id": event.session_id,
        })

    return jsonify(result), 200


@dashboard_bp.route(
    "/soc/access-history",
    methods=["GET"],
)
@login_required
def soc_access_history():
    """Return recent protected-resource events across all users."""
    auth_err = _soc_require_admin()

    if auth_err:
        return auth_err

    events = (
        AccessEvent.query
        .order_by(
            AccessEvent.timestamp.desc(),
            AccessEvent.id.desc(),
        )
        .limit(20)
        .all()
    )

    result = []

    for event in events:
        result.append({
            "event_id": event.id,
            "timestamp": (
                event.timestamp.isoformat()
                if event.timestamp
                else None
            ),
            "user_id": event.user_id,
            "username": _soc_username(event.user_id),
            "session_id": event.session_id,
            "resource": event.resource,
            "decision": event.decision,
            "risk_score": event.risk_score,
            "privilege_mismatch":
                bool(event.privilege_mismatch),
            "ip_address": event.ip_address,
            "device_id": event.device_id,
        })

    return jsonify(result), 200


@dashboard_bp.route(
    "/soc/security-state",
    methods=["GET"],
)
@login_required
def soc_security_state():
    """Return the latest analyzed application access event globally."""
    auth_err = _soc_require_admin()

    if auth_err:
        return auth_err

    latest_event = (
        AccessEvent.query
        .order_by(
            AccessEvent.timestamp.desc(),
            AccessEvent.id.desc(),
        )
        .first()
    )

    if latest_event is None:
        return jsonify({
            "session_id": None,
            "user_id": None,
            "username": None,
            "risk_label": None,
            "risk_score": None,
            "anomaly_score": None,
            "cluster_id": None,
            "latest_action": None,
            "latest_resource": None,
            "latest_access_at": None,
            "privilege_mismatch": False,
            "is_active": False,
            "has_analysis": False,
        }), 200

    session_row = (
        Session.query
        .filter_by(
            session_id=latest_event.session_id,
            user_id=latest_event.user_id,
        )
        .first()
    )

    login_event = None

    if (
        session_row is not None
        and session_row.login_event_id is not None
    ):
        login_event = (
            LoginEvent.query
            .filter_by(id=session_row.login_event_id)
            .first()
        )

    risk_label = None
    risk_score = latest_event.risk_score
    anomaly_score = None
    cluster_id = None
    is_active = False

    if session_row is not None:
        risk_label = session_row.current_risk_label

        if session_row.current_risk_score is not None:
            risk_score = session_row.current_risk_score

        is_active = bool(session_row.is_active)

    if login_event is not None:
        if risk_label is None:
            risk_label = login_event.risk_label

        anomaly_score = login_event.anomaly_score
        cluster_id = login_event.cluster_id

    has_analysis = any(
        value is not None
        for value in (
            risk_label,
            risk_score,
            anomaly_score,
            cluster_id,
        )
    )

    return jsonify({
        "session_id": latest_event.session_id,
        "user_id": latest_event.user_id,
        "username": _soc_username(latest_event.user_id),
        "risk_label": risk_label,
        "risk_score": risk_score,
        "anomaly_score": anomaly_score,
        "cluster_id": cluster_id,
        "latest_action": latest_event.decision,
        "latest_resource": latest_event.resource,
        "latest_access_at": (
            latest_event.timestamp.isoformat()
            if latest_event.timestamp
            else None
        ),
        "privilege_mismatch":
            bool(latest_event.privilege_mismatch),
        "is_active": is_active,
        "has_analysis": has_analysis,
    }), 200


@dashboard_bp.route(
    "/soc/security-alerts",
    methods=["GET"],
)
@login_required
def soc_security_alerts():
    """Return organization-wide persisted Zero Trust alerts."""
    auth_err = _soc_require_admin()

    if auth_err:
        return auth_err

    events = (
        AccessEvent.query
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
            AccessEvent.timestamp.desc(),
            AccessEvent.id.desc(),
        )
        .limit(20)
        .all()
    )

    result = []

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
                "Resource access restricted by Zero Trust policy."
            )

        elif bool(event.privilege_mismatch):
            severity = "high"
            alert_type = "PRIVILEGE_MISMATCH"
            message = (
                "Unauthorized role attempted protected resource access."
            )

        elif decision == "OTP":
            severity = "medium"
            alert_type = "OTP_REQUIRED"
            message = (
                "Step-up OTP verification required."
            )

        else:
            continue

        result.append({
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
            "policy_action": decision,
            "risk_score": event.risk_score,
            "privilege_mismatch":
                bool(event.privilege_mismatch),
            "session_id": event.session_id,
            "user_id": event.user_id,
            "username": _soc_username(event.user_id),
        })

    return jsonify(result), 200

@dashboard_bp.route(
    "/soc/sessions-history",
    methods=["GET"],
)
@login_required
def soc_sessions_history():
    """Return recent historical sessions across all application users."""
    auth_err = _soc_require_admin()

    if auth_err:
        return auth_err

    sessions = (
        Session.query
        .order_by(
            Session.started_at.desc(),
            Session.id.desc(),
        )
        .limit(50)
        .all()
    )

    result = []

    for row in sessions:
        result.append({
            "session_id": row.session_id,
            "user_id": row.user_id,
            "username": _soc_username(row.user_id),
            "started_at": (
                row.started_at.isoformat()
                if row.started_at
                else None
            ),
            "ended_at": (
                row.ended_at.isoformat()
                if row.ended_at
                else None
            ),
            "current_ip": row.current_ip,
            "current_device_fingerprint": row.current_device_fingerprint,
            "risk_label": row.current_risk_label,
            "risk_score": row.current_risk_score,
            "is_active": bool(row.is_active),
            "end_reason": getattr(row, "end_reason", None)
        })

    return jsonify(result), 200
