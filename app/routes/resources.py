from datetime import datetime

from flask import Blueprint, jsonify, request, session as flask_session
from flask_login import current_user, login_required

from app.extensions import db
from app.models import AccessEvent, Session
from app.services.policy_enforcement import apply_zero_trust_policy
from app.services.risk_analysis import analyze_operational_access
from app.utils.fingerprint import get_device_fingerprint
from app.utils.forensics_utils import preserve_evidence


resources_bp = Blueprint(
    "resources",
    __name__,
    url_prefix="/api/resources",
)


# Resource sensitivity and RBAC authorization are intentionally separate.
#
# resource_sensitivity:
#     Behavioral/risk context used by the operational ML feature pipeline.
#
# allowed_roles:
#     Authorization truth used to create privilege_mismatch evidence.
#
# Finance remains high sensitivity but available to ordinary roles so the
# Zero Trust system can continuously evaluate legitimate sensitive access.

RESOURCE_SENSITIVITY = {
    "normal_page": "low",
    "hr_page": "medium",
    "finance_page": "high",
    "admin_page": "high",
    "confidential_page": "high",
}


RESOURCE_ALLOWED_ROLES = {
    "normal_page": {
        "admin",
        "employee",
        "finance_user",
        "guest",
        "hr_user",
    },
    "hr_page": {
        "admin",
        "employee",
        "finance_user",
        "guest",
        "hr_user",
    },
    "finance_page": {
        "admin",
        "employee",
        "finance_user",
        "guest",
        "hr_user",
    },
    "admin_page": {
        "admin",
    },
}


RESOURCE_MESSAGES = {
    "normal_page": (
        "Normal Employee Page",
        "General company info, visible to all employees.",
    ),
    "hr_page": (
        "HR Page",
        "HR records and policies.",
    ),
    "finance_page": (
        "Finance Page",
        "Sensitive financial records.",
    ),
    "admin_page": (
        "Admin Page",
        "System administration panel.",
    ),
}


def _get_session_id() -> str:
    """Return the application Session identifier created at login."""

    return flask_session.get(
        "app_session_id",
        "unknown-session",
    )


def _is_privilege_mismatch(
    resource: str,
) -> bool:
    """Return whether the authenticated role is unauthorized."""

    allowed_roles = RESOURCE_ALLOWED_ROLES.get(
        resource,
        set(),
    )

    return current_user.role not in allowed_roles


def _detect_and_update_session_changes(
    session_id: str,
    current_ip: str,
    current_device_fp: str,
) -> tuple[bool, bool]:
    """Detect continuous-session IP/device changes."""

    session_row = (
        Session.query
        .filter_by(
            session_id=session_id,
            is_active=True,
        )
        .first()
    )

    if not session_row:
        return False, False

    ip_changed = (
        session_row.current_ip
        != current_ip
    )

    device_changed = (
        session_row.current_device_fingerprint
        != current_device_fp
    )

    session_row.current_ip = current_ip
    session_row.current_device_fingerprint = (
        current_device_fp
    )

    db.session.commit()

    return (
        ip_changed,
        device_changed,
    )


def _log_access(
    resource: str,
    decision: str = None,
) -> AccessEvent:
    """Persist one protected-resource access event."""

    sensitivity = RESOURCE_SENSITIVITY.get(
        resource,
        "low",
    )

    user_agent = request.headers.get(
        "User-Agent",
        "",
    )

    device_fp = get_device_fingerprint(
        user_agent
    )

    ip = request.remote_addr or "unknown"
    session_id = _get_session_id()

    (
        ip_changed,
        device_changed,
    ) = _detect_and_update_session_changes(
        session_id,
        ip,
        device_fp,
    )

    event = AccessEvent(
        user_id=current_user.id,
        session_id=session_id,
        resource=resource,
        resource_sensitivity=sensitivity,
        timestamp=datetime.utcnow(),
        ip_address=ip,
        device_id=request.headers.get(
            "User-Agent",
            "unknown",
        ),
        device_fingerprint=device_fp,
        privilege_mismatch=_is_privilege_mismatch(
            resource
        ),
        ip_changed=ip_changed,
        device_changed=device_changed,
        decision=decision,
    )

    db.session.add(event)
    db.session.flush()

    session_row = (
        Session.query
        .filter_by(
            session_id=session_id,
        )
        .first()
    )

    anchor_login_id = (
        session_row.login_event_id
        if session_row
        else None
    )

    if anchor_login_id:
        details = {
            "event_type": "AccessEvent",
            "access_event_id": event.id,
            "session_id": event.session_id,
            "user_id": event.user_id,
            "resource": event.resource,
            "timestamp": event.timestamp.isoformat(),
            "ip_address": event.ip_address,
            "device_fingerprint": (
                event.device_fingerprint
            ),
            "privilege_mismatch": (
                event.privilege_mismatch
            ),
            "ip_changed": event.ip_changed,
            "device_changed": (
                event.device_changed
            ),
        }

        preserve_evidence(
            anchor_login_id,
            details,
        )

    db.session.commit()

    return event


def _log_and_analyze_access(
    resource: str,
):
    """Persist an access event and run operational ML analysis."""

    event = _log_access(
        resource
    )

    analysis = analyze_operational_access(
        session_id=event.session_id,
        access_event_id=event.id,
    )

    return (
        event,
        analysis,
    )


def _log_analyze_and_enforce_access(
    resource: str,
):
    """Run event -> ML -> policy persistence/enforcement."""

    (
        event,
        analysis,
    ) = _log_and_analyze_access(
        resource
    )

    policy_result = apply_zero_trust_policy(
        session_id=event.session_id,
        access_event_id=event.id,
        analysis=analysis,
    )

    return (
        event,
        analysis,
        policy_result,
    )


def _resource_response(
    resource_key: str,
):
    """Apply Zero Trust before releasing a protected resource."""

    (
        _event,
        _analysis,
        policy_result,
    ) = _log_analyze_and_enforce_access(
        resource_key
    )

    action = policy_result[
        "action"
    ]

    if action == "OTP":
        return jsonify({
            "error": "OTP verification required.",
            "policy_action": "OTP",
            "requires_otp": True,
        }), 401

    if action == "Restrict":
        return jsonify({
            "error": (
                "Access restricted by Zero Trust policy."
            ),
            "policy_action": "Restrict",
        }), 403

    if action == "Block":
        return jsonify({
            "error": (
                "Session blocked by Zero Trust policy."
            ),
            "policy_action": "Block",
        }), 401

    if action != "Allow":
        raise RuntimeError(
            f"Unsupported Zero Trust policy action: {action}"
        )

    title, message = RESOURCE_MESSAGES[
        resource_key
    ]

    return jsonify({
        "title": title,
        "sensitivity": RESOURCE_SENSITIVITY[
            resource_key
        ],
        "message": message,
    }), 200


@resources_bp.route(
    "/normal",
    methods=["GET"],
)
@login_required
def normal_page():
    return _resource_response(
        "normal_page"
    )


@resources_bp.route(
    "/hr",
    methods=["GET"],
)
@login_required
def hr_page():
    return _resource_response(
        "hr_page"
    )


@resources_bp.route(
    "/finance",
    methods=["GET"],
)
@login_required
def finance_page():
    return _resource_response(
        "finance_page"
    )


@resources_bp.route(
    "/admin",
    methods=["GET"],
)
@login_required
def admin_page():
    # Authorization is now represented as privilege_mismatch
    # evidence and enforced by the unified Zero Trust policy.
    return _resource_response(
        "admin_page"
    )
