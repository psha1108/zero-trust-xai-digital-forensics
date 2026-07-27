import hashlib
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models import AccessEvent

resources_bp = Blueprint("resources", __name__, url_prefix="/api/resources")

RESOURCE_SENSITIVITY = {
    "normal_page": "low",
    "hr_page": "medium",
    "finance_page": "high",
    "admin_page": "high",
    "confidential_page": "high",
}

RESOURCE_MESSAGES = {
    "normal_page": ("Normal Employee Page", "General company info, visible to all employees."),
    "hr_page": ("HR Page", "HR records and policies."),
    "finance_page": ("Finance Page", "Sensitive financial records."),
    "admin_page": ("Admin Page", "System administration panel."),
}


def _get_session_id() -> str:
    raw_cookie = request.cookies.get("session", "unknown-session")
    return hashlib.sha256(raw_cookie.encode()).hexdigest()


def _log_access(resource: str) -> AccessEvent:
    event = AccessEvent(
        user_id=current_user.id,
        session_id=_get_session_id(),
        resource=resource,
        resource_sensitivity=RESOURCE_SENSITIVITY.get(resource, "low"),
        timestamp=datetime.utcnow(),
        ip_address=request.remote_addr or "unknown",
        device_id=request.headers.get("User-Agent", "unknown"),
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
        _log_access("admin_page")
        return jsonify({"error": "Forbidden — admin role required."}), 403
    return _resource_response("admin_page")