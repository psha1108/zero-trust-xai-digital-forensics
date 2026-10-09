from datetime import datetime
from flask import Blueprint, request, jsonify, session as flask_session
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models import User, LoginEvent, Session
from app.services.otp_service import verify_otp_code, cancel_otp_challenge, create_otp_challenge, _latest_unverified_challenge
from app.utils.fingerprint import get_device_fingerprint, generate_session_id
from app.utils.forensics_utils import preserve_evidence

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _log_login_event(username_attempted: str, success: bool, user_id: int | None, role: str | None = None, client_id: str | None = None, failed_login_count: int = 0) -> LoginEvent:
    event = LoginEvent(
        user_id=user_id,
        username_attempted=username_attempted,
        timestamp=datetime.utcnow(),
        ip_address=request.remote_addr or "unknown",
        device_info=request.headers.get("User-Agent", "unknown"),
        success=success,
    )
    db.session.add(event)
    db.session.flush()
    
    details = {
        "event": {
            "event_id": event.id,
            "event_type": "LoginEvent",
            "timestamp": event.timestamp.isoformat(),
            "session_id": None
        },
        "user": {
            "user_id": event.user_id,
            "username": event.username_attempted,
            "role": role
        },
        "network": {
            "ip_address": event.ip_address,
            "ip_changed_during_session": False
        },
        "device": {
            "device_info": event.device_info,
            "device_changed_during_session": False
        },
        "security": {
            "success": event.success,
            "failed_login_count": failed_login_count
        }
    }
    if client_id == 'soc':
        import json
        from app.models import SocAuditLog
        audit_event = SocAuditLog(
            user_id=user_id,
            action="SOC Login",
            timestamp=datetime.utcnow(),
            details=json.dumps(details)
        )
        db.session.add(audit_event)
    else:
        preserve_evidence(event.id, details)
        
    db.session.commit()
    return event


import re

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not username or not email or not password:
        return jsonify({"error": "All fields are required."}), 400

    username_regex = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{3,19}$")
    if not username_regex.match(username):
        return jsonify({"error": "Invalid username format."}), 400

    email_regex = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    if not email_regex.match(email):
        return jsonify({"error": "Invalid email format."}), 400

    password_regex = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$")
    if not password_regex.match(password):
        return jsonify({"error": "Password does not meet requirements."}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Username or email already exists."}), 409

    user = User(username=username, email=email, role="employee")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registration successful."}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}



    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    client_id = (data.get("client_id") or "").strip()

    user = User.query.filter_by(username=username).first()
    success = user is not None and user.check_password(password)

    failed_count = 0
    if user:
        last_events = LoginEvent.query.filter_by(user_id=user.id).order_by(LoginEvent.timestamp.desc()).limit(10).all()
        for e in last_events:
            if e.success:
                if e.action_taken == "OTP Required" and e.session_id:
                    from app.models import OtpChallenge
                    challenge = OtpChallenge.query.filter_by(
                        session_id=e.session_id, resource="login"
                    ).order_by(OtpChallenge.id.desc()).first()
                    
                    if challenge and challenge.verified_at is None:
                        continue
                break
            failed_count += 1

    event = _log_login_event(
        username_attempted=username,
        success=success,
        user_id=user.id if user else None,
        role=user.role if user else None,
        client_id=client_id,
        failed_login_count=failed_count
    )

    if success:
        if failed_count < 3:
            login_user(user)

        # Create the Session row — this is the real "start of a continuous
        # Zero Trust session," not just a login event. Everything from here
        # (mid-session risk re-evaluation, forced termination) hinges on
        # this row existing.
        new_session_id = generate_session_id()
        flask_session["app_session_id"] = new_session_id

        device_fp = get_device_fingerprint(request.headers.get("User-Agent", ""))
        ip = request.remote_addr or "unknown"

        event.session_id = new_session_id
        
        if failed_count >= 3:
            event.risk_label = "Medium"
            event.action_taken = "OTP Required"

        db.session.add(Session(
            session_id=new_session_id,
            user_id=user.id,
            login_event_id=event.id,
            started_at=datetime.utcnow(),
            start_ip=ip,
            current_ip=ip,
            start_device_fingerprint=device_fp,
            current_device_fingerprint=device_fp,
            is_active=True,
        ))
        db.session.commit()

        if failed_count >= 3:
            from app.services.otp_service import create_otp_challenge
            create_otp_challenge(
                session_id=new_session_id,
                user_id=user.id,
                resource="login",
                delivery_target=user.email,
                reason_codes=["Repeated failed login attempts"]
            )
            return jsonify({
                "message": "OTP required.",
                "require_otp": True,
                "user": {"id": user.id, "username": user.username, "role": user.role},
            }), 202

        return jsonify({
            "message": "Login successful.",
            "user": {"id": user.id, "username": user.username, "role": user.role},
        }), 200

    logout_user()
    flask_session.pop("app_session_id", None)

    return jsonify({"error": "Invalid username or password."}), 401


@auth_bp.route("/otp/verify", methods=["POST"])
def verify_otp():
    """Verify the active session's pending Zero Trust OTP."""

    data = request.get_json(
        silent=True
    ) or {}

    otp_code = data.get(
        "otp_code"
    )

    if (
        not isinstance(otp_code, str)
        or len(otp_code) != 6
        or not otp_code.isascii()
        or not otp_code.isdigit()
    ):
        return jsonify({
            "error": "A 6-digit OTP is required.",
        }), 400

    session_id = flask_session.get(
        "app_session_id"
    )

    session_row = Session.query.filter_by(session_id=session_id, is_active=True).first()
    if not session_row:
        return jsonify({
            "error": "Session invalid. Please log in again.",
        }), 401
        
    user_id = session_row.user_id

    result = verify_otp_code(
        session_id=session_id,
        user_id=user_id,
        otp_code=otp_code,
    )

    status = result[
        "status"
    ]

    if result["verified"] is True:
        # If this was a login OTP, authenticate the user now.
        from app.models import OtpChallenge
        challenge = OtpChallenge.query.filter_by(
            session_id=session_id, user_id=user_id
        ).order_by(OtpChallenge.verified_at.desc()).first()
        
        if challenge and challenge.resource == "login":
            user = User.query.get(user_id)
            if user:
                login_user(user)
                
        details = {
            "event": {"event_type": "OTP_VERIFIED"},
            "session_id": session_id,
            "user_id": user_id
        }
        preserve_evidence(session_row.login_event_id, details)
            
        return jsonify({
            "message": "OTP verified.",
            "verified": True,
        }), 200

    if status == "invalid":
        details = {
            "event": {"event_type": "OTP_VERIFICATION_FAILED"},
            "session_id": session_id,
            "user_id": user_id
        }
        preserve_evidence(session_row.login_event_id, details)
            
        return jsonify({
            "error": "Invalid OTP.",
            "verified": False,
            "attempts_remaining": result[
                "attempts_remaining"
            ],
        }), 400

    if status == "locked":
        session_row = Session.query.filter_by(session_id=session_id, is_active=True).first()
        if session_row:
            session_row.is_active = False
            session_row.ended_at = datetime.utcnow()
            session_row.end_reason = "OTP_FAILED_ATTEMPTS"
            
            details = {
                "event": {
                    "event_type": "SessionTermination",
                },
                "session_id": session_id,
                "timestamp": session_row.ended_at.isoformat(),
                "user": {
                    "user_id": user_id,
                    "username": user.username if (user := User.query.get(user_id)) else "unknown",
                    "role": user.role if user else "unknown"
                },
                "policy_action": "OTP",
                "session_outcome": "Terminated",
                "termination_reason": "OTP_FAILED_ATTEMPTS",
                "explanation": "Step-up verification was required based on the security assessment. The session was subsequently terminated because the maximum permitted OTP verification attempts were unsuccessful.",
                "previous_session_state": "Active",
                "current_session_state": "Inactive"
            }
            preserve_evidence(session_row.login_event_id, details)
            
            db.session.commit()

        return jsonify({
            "error": "OTP challenge locked.",
            "verified": False,
            "attempts_remaining": 0,
        }), 423

    if status == "expired":
        details = {
            "event": {"event_type": "OTP_EXPIRED"},
            "session_id": session_id,
            "user_id": user_id
        }
        preserve_evidence(session_row.login_event_id, details)
            
        return jsonify({
            "error": "OTP challenge expired.",
            "verified": False,
            "attempts_remaining": 0,
        }), 410

    raise RuntimeError(
        f"Unsupported OTP verification status: {status}"
    )

@auth_bp.route("/otp/resend", methods=["POST"])
def resend_otp():
    session_id = flask_session.get("app_session_id")
    if not session_id:
        return jsonify({"error": "Session invalid."}), 401
        
    session_row = Session.query.filter_by(session_id=session_id, is_active=True).first()
    if not session_row:
        return jsonify({"error": "Session invalid."}), 401
        
    user_id = session_row.user_id

    challenge = _latest_unverified_challenge(session_id=session_id, user_id=user_id)
    if challenge:
        # Check 60-second cooldown
        now = datetime.utcnow()
        elapsed = (now - challenge.created_at).total_seconds()
        if elapsed < 60:
            return jsonify({"error": "Please wait 60 seconds before requesting another code."}), 429
            
        resource = challenge.resource
        result = create_otp_challenge(
            session_id=session_id,
            user_id=user_id,
            resource=resource,
            delivery_target=User.query.get(user_id).email,
            reason_codes=challenge.granted_reason_codes.split(",") if challenge.granted_reason_codes else [],
            force_new=True
        )
        
        return jsonify(result), 200
        
    return jsonify({"error": "No pending challenge found."}), 404


@auth_bp.route("/otp/cancel", methods=["POST"])
def cancel_otp():
    session_id = flask_session.get("app_session_id")
    if not session_id:
        return jsonify({"error": "Session invalid."}), 401
        
    session_row = Session.query.filter_by(session_id=session_id, is_active=True).first()
    if not session_row:
        return jsonify({"error": "Session invalid."}), 401
        
    user_id = session_row.user_id
        
    success = cancel_otp_challenge(session_id=session_id, user_id=user_id)
    
    if success:
        details = {
            "event": {"event_type": "OTP_CANCELLED"},
            "session_id": session_id,
            "user_id": user_id
        }
        preserve_evidence(session_row.login_event_id, details)
            
        return jsonify({"message": "OTP challenge cancelled."}), 200
        
    return jsonify({"error": "No pending challenge to cancel."}), 404


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    Closes the Session row properly — this is what makes 'ended_at',
    'end_reason', and 'is_active' actually mean something, instead of
    sitting unused since the sessions-table branch. Also back-fills
    login_events.session_duration_sec now that we know how long the
    session actually lasted.
    """
    session_id = flask_session.get("app_session_id")

    if session_id:
        session_row = Session.query.filter_by(
            session_id=session_id, is_active=True
        ).first()

        if session_row:
            session_row.ended_at = datetime.utcnow()
            session_row.end_reason = "logout"
            session_row.is_active = False

            duration_sec = int(
                (session_row.ended_at - session_row.started_at).total_seconds()
            )

            login_event = LoginEvent.query.get(session_row.login_event_id)
            if login_event:
                login_event.session_duration_sec = duration_sec

            db.session.commit()

    logout_user()
    flask_session.pop("app_session_id", None)

    return jsonify({"message": "Logged out."}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    """
    Lets React ask "who am I / am I still logged in?" — needed because
    React apps reload in the browser and lose in-memory state, but the
    session cookie persists, so this endpoint restores that knowledge.
    """
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
    }), 200
