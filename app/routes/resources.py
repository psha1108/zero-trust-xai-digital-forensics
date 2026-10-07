from datetime import datetime

from flask import Blueprint, jsonify, request, session as flask_session
from flask_login import current_user, login_required

from app.extensions import db
from app.models import AccessEvent, Session
from app.services.otp_service import (
    create_otp_challenge,
    has_valid_otp_grant,
)
from app.services.policy_enforcement import apply_zero_trust_policy
from app.services.risk_analysis import analyze_operational_access
from app.services.explanations import generate_shap_explanation, generate_policy_explanation
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
    "management_reports": "high",
    "confidential_page": "high",
    "it_support": "low",
    "tasks_page": "low",
    "policies_page": "low",
    "announcements_page": "low",
}


RESOURCE_ALLOWED_ROLES = {
    "normal_page": {
        "admin",
        "employee",
    },
    "hr_page": {
        "admin",
        "hr_user",
    },
    "finance_page": {
        "admin",
        "finance_user",
    },
    "admin_page": {
        "admin",
    },
    "management_reports": {
        "admin",
    },
    "it_support": {
        "admin",
    },
    "tasks_page": {
        "admin",
        "employee",
        "finance_user",
        "guest",
        "hr_user",
    },
    "policies_page": {
        "admin",
        "employee",
        "finance_user",
        "guest",
        "hr_user",
    },
    "announcements_page": {
        "admin",
        "employee",
        "finance_user",
        "guest",
        "hr_user",
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
    "management_reports": (
        "Management Reports",
        "Internal management reports for authorized finance and administrative personnel.",
    ),
    "it_support": (
        "IT Support",
        "Access IT policies, device guidelines, and support resources.",
    ),
    "tasks_page": (
        "My Tasks",
        "Your current ACME Technologies work items.",
    ),
    "policies_page": (
        "Company Policies",
        "Employee policies and workplace guidance.",
    ),
    "announcements_page": (
        "Announcements",
        "Company news and employee notices.",
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

    # 8. Create final Evidence Snapshot for AccessEvent
    session_row = Session.query.filter_by(session_id=event.session_id).first()
    anchor_login_id = session_row.login_event_id if session_row else None

    if anchor_login_id:
        details = {
            "event": {
                "event_id": event.id,
                "event_type": "AccessEvent",
            },
            "access_event_id": event.id,
            "session_id": event.session_id,
            "user_id": event.user_id,
            "user": {
                "user_id": event.user_id,
                "username": current_user.username,
                "role": current_user.role
            },
            "timestamp": event.timestamp.isoformat(),
            "resource": {
                "name": event.resource,
                "sensitivity": event.resource_sensitivity
            },
            "network": {
                "ip_address": event.ip_address,
                "ip_changed_during_session": event.ip_changed
            },
            "device": {
                "device_id": event.device_id,
                "device_fingerprint": event.device_fingerprint,
                "device_changed_during_session": event.device_changed
            },
            "security": {
                "privilege_mismatch": event.privilege_mismatch,
                "unauthorized_access_attempt": False
            },
            "access": {
                "request_count": analysis.get("features", {}).get("access_count_5min", 0)
            },
            "ml": {
                "isolation_forest": {
                    "anomaly_score": analysis.get("anomaly_detection", {}).get("anomaly_score"),
                    "is_anomaly": analysis.get("anomaly_detection", {}).get("is_anomaly")
                },
                "random_forest": {
                    "risk_label": analysis.get("prediction", {}).get("predicted_risk"),
                    "risk_score": analysis.get("prediction", {}).get("probability_high")
                },
                "kmeans": {
                    "cluster_id": analysis.get("behavioral_cluster", {}).get("cluster_id"),
                    "behavior_label": analysis.get("behavioral_cluster", {}).get("archetype_name")
                }
            },
            "shap": analysis.get("explanation", {}),
            "zero_trust": {
                "policy_decision": policy_result.get("action"),
                "reason": ", ".join(policy_result.get("reason_codes", [])) if policy_result.get("reason_codes") else "No reason provided",
                "http_status": 200 if policy_result.get("action") == "Allow" else (
                    403 if policy_result.get("action") == "Restrict" else (
                        200 if policy_result.get("action") == "OTP" and has_valid_otp_grant(session_id=event.session_id, user_id=current_user.id, resource=event.resource) else 401
                    )
                )
            }
        }
        
        details["shap"]["human_explanation"] = generate_shap_explanation(details["shap"])
        details["zero_trust"]["human_reason"] = generate_policy_explanation(
            details["zero_trust"]["policy_decision"],
            policy_result.get("reason_codes", [])
        )
        
        preserve_evidence(anchor_login_id, details)
        
    # 9. Handle session termination AFTER evidence preservation
    if policy_result.get("terminate_session") and session_row:
        session_row.is_active = False
        if session_row.ended_at is None:
            session_row.ended_at = datetime.utcnow()
        session_row.end_reason = "blocked"

    db.session.commit()

    return (
        event,
        analysis,
        policy_result,
    )


def _successful_resource_response(
    resource_key: str,
):
    """Return the existing successful protected-resource payload."""

    title, message = RESOURCE_MESSAGES[
        resource_key
    ]

    response_data = {
        "title": title,
        "sensitivity": RESOURCE_SENSITIVITY[resource_key],
        "message": message,
    }

    if resource_key == "management_reports":
        response_data["dummy_data"] = {
            "monthly_active_users": 1542,
            "system_uptime": "99.99%",
            "incidents_blocked": 42,
            "revenue_impact": "$1.2M",
            "report_date": datetime.utcnow().isoformat()
        }

    return jsonify(response_data), 200


def _resource_response(
    resource_key: str,
):
    """Apply Zero Trust and satisfy OTP only with a valid grant."""
    
    session_id = _get_session_id()
    session_row = Session.query.filter_by(
        session_id=session_id, is_active=True
    ).first()
    
    if not session_row:
        return jsonify({
            "error": "Session is invalid or has been terminated.",
            "policy_action": "Block"
        }), 401

    (
        event,
        _analysis,
        policy_result,
    ) = _log_analyze_and_enforce_access(
        resource_key
    )

    action = policy_result[
        "action"
    ]

    if action == "OTP":
        if has_valid_otp_grant(
            session_id=event.session_id,
            user_id=current_user.id,
            resource=resource_key,
            current_reason_codes=policy_result.get("reason_codes", []),
        ):
            return _successful_resource_response(
                resource_key
            )

        create_otp_challenge(
            session_id=event.session_id,
            user_id=current_user.id,
            resource=resource_key,
            delivery_target=current_user.email,
            reason_codes=policy_result.get("reason_codes", []),
        )

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

    return _successful_resource_response(
        resource_key
    )


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
    "/management-reports",
    methods=["GET"],
)
@login_required
def management_reports():
    """Protected management reporting resource."""
    return _resource_response(
        "management_reports"
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


@resources_bp.route(
    "/it-support",
    methods=["GET"],
)
@login_required
def it_support_page():
    """Protected IT support resource."""
    return _resource_response(
        "it_support"
    )


@resources_bp.route(
    "/tasks",
    methods=["GET"],
)
@login_required
def tasks_page():
    """Protected tasks resource."""
    return _resource_response(
        "tasks_page"
    )


@resources_bp.route(
    "/policies",
    methods=["GET"],
)
@login_required
def policies_page():
    """Protected policies resource."""
    return _resource_response(
        "policies_page"
    )


@resources_bp.route(
    "/announcements",
    methods=["GET"],
)
@login_required
def announcements_page():
    """Protected announcements resource."""
    return _resource_response(
        "announcements_page"
    )

