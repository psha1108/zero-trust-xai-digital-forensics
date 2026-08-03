from datetime import datetime
from flask import Blueprint, request, jsonify, session as flask_session
from flask_login import login_required, current_user

from app.extensions import db
from app.models import AccessEvent, Session
from app.utils.fingerprint import get_device_fingerprint

resources_bp = Blueprint("resources", __name__, url_prefix="/api/resources")

# Two SEPARATE concerns, deliberately kept apart:
#
# 1. resource_sensitivity — feeds the risk SCORE. High sensitivity means
#    "this activity should weigh more heavily," not "this is forbidden."
#    Finance is intentionally high-sensitivity AND open to normal users,
#    specifically so we can observe and score risky behavior around it.
#
# 2. allowed_roles — actual RBAC. privilege_mismatch is TRUE only when a
#    role tries to access a resource it's genuinely not authorized for.
#    Right now, only Admin is role-restricted.

RESOURCE_SENSITIVITY = {
    "normal_page": "low",
    "hr_page": "medium",
    "finance_page": "high",
    "admin_page": "high",
    "confidential_page": "high",
}

RESOURCE_ALLOWED_ROLES = {
    "normal_page": {"user", "admin"},
    "hr_page": {"user", "admin"},
    "finance_page": {"user", "admin"},   # intentionally open — high sensitivity, no restriction
    "admin_page": {"admin"},              # the only genuinely restricted resource right now
}

RESOURCE_MESSAGES = {
    "normal_page": ("Normal Employee Page", "General company info, visible to all employees."),
    "hr_page": ("HR Page", "HR records and policies."),
    "finance_page": ("Finance Page", "Sensitive financial records."),
    "admin_page": ("Admin Page", "System administration panel."),
}

def _get_session_id() -> str:
    """
    Reads the session_id we generated and stored at login time (see
    auth.py) instead of hashing the raw cookie. This guarantees it
    matches the value stored in the sessions table.
    """
    return flask_session.get("app_session_id", "unknown-session")


def _is_privilege_mismatch(resource: str) -> bool:
    allowed_roles = RESOURCE_ALLOWED_ROLES.get(resource, set())
    return current_user.role not in allowed_roles


def _detect_and_update_session_changes(session_id: str, current_ip: str, current_device_fp: str) -> tuple[bool, bool]:
    """
    Compares this request's IP/device against what the session last had on
    record, updates the session to the new values, and reports whether
    either one changed. This is the actual "continuous" part of continuous
    Zero Trust — a session that started from one IP/device and suddenly
    shows a different one mid-session is exactly the signal this project
    is meant to catch.
    """
    session_row = Session.query.filter_by(session_id=session_id, is_active=True).first()
    if not session_row:
        return False, False

    ip_changed = session_row.current_ip != current_ip
    device_changed = session_row.current_device_fingerprint != current_device_fp

    session_row.current_ip = current_ip
    session_row.current_device_fingerprint = current_device_fp
    db.session.commit()

    return ip_changed, device_changed


def _log_access(resource: str) -> AccessEvent:
    sensitivity = RESOURCE_SENSITIVITY.get(resource, "low")
    device_fp = get_device_fingerprint(request.headers.get("User-Agent", ""))
    ip = request.remote_addr or "unknown"
    session_id = _get_session_id()

    ip_changed, device_changed = _detect_and_update_session_changes(session_id, ip, device_fp)

    event = AccessEvent(
        user_id=current_user.id,
        session_id=session_id,
        resource=resource,
        resource_sensitivity=sensitivity,
        timestamp=datetime.utcnow(),
        ip_address=ip,
        device_id=request.headers.get("User-Agent", "unknown"),
        device_fingerprint=device_fp,
        privilege_mismatch=_is_privilege_mismatch(resource),
        ip_changed=ip_changed,
        device_changed=device_changed,
    )
    db.session.add(event)
    db.session.commit()
    return event


def _resource_response(resource_key: str):
    _log_access(resource_key)
    title, message = RESOURCE_MESSAGES[resource_key]
    return jsonify({
        "title": title,
        "sensitivity": RESOURCE_SENSITIVITY[resource_key],
        "message": message,
    }), 200


@resources_bp.route("/normal", methods=["GET"])
@login_required
def normal_page():
    return _resource_response("normal_page")


@resources_bp.route("/hr", methods=["GET"])
@login_required
def hr_page():
    return _resource_response("hr_page")


@resources_bp.route("/finance", methods=["GET"])
@login_required
def finance_page():
    return _resource_response("finance_page")


@resources_bp.route("/admin", methods=["GET"])
@login_required
def admin_page():
    if current_user.role != "admin":
        _log_access("admin_page")  # still logged — privilege_mismatch will be True
        return jsonify({"error": "Forbidden — admin role required."}), 403
    return _resource_response("admin_page")