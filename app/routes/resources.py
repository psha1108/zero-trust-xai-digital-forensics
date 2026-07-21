import hashlib
from datetime import datetime
from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import AccessEvent

resources_bp = Blueprint("resources", __name__)

RESOURCE_SENSITIVITY = {
    "normal_page": "low",
    "hr_page": "medium",
    "finance_page": "high",
    "admin_page": "high",
    "confidential_page": "high",
}


def _get_session_id() -> str:
    """
    Flask's raw session cookie can be 150+ characters (it's the full
    signed/encrypted cookie), which doesn't fit in a short DB column.
    We hash it down to a fixed 64-character SHA-256 hex digest instead —
    still uniquely identifies the session, just fixed-length.
    """
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


@resources_bp.route("/resources/normal")
@login_required
def normal_page():
    _log_access("normal_page")
    return render_template("resource.html", title="Normal Employee Page",
                            sensitivity="Low", message="General company info, visible to all employees.")


@resources_bp.route("/resources/hr")
@login_required
def hr_page():
    _log_access("hr_page")
    return render_template("resource.html", title="HR Page",
                            sensitivity="Medium", message="HR records and policies.")


@resources_bp.route("/resources/finance")
@login_required
def finance_page():
    _log_access("finance_page")
    return render_template("resource.html", title="Finance Page",
                            sensitivity="High", message="Sensitive financial records.")


@resources_bp.route("/resources/admin")
@login_required
def admin_page():
    if current_user.role != "admin":
        _log_access("admin_page")
        abort(403)
    _log_access("admin_page")
    return render_template("resource.html", title="Admin Page",
                            sensitivity="High", message="System administration panel.")