from datetime import datetime
from flask import Blueprint, request, jsonify, session as flask_session
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models import User, LoginEvent, Session
from app.utils.fingerprint import get_device_fingerprint, generate_session_id
from app.utils.forensics_utils import preserve_evidence

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _log_login_event(username_attempted: str, success: bool, user_id: int | None) -> LoginEvent:
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
        "event_type": "LoginEvent",
        "login_event_id": event.id,
        "user_id": event.user_id,
        "username_attempted": event.username_attempted,
        "timestamp": event.timestamp.isoformat(),
        "ip_address": event.ip_address,
        "device_info": event.device_info,
        "success": event.success
    }
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

    user = User.query.filter_by(username=username).first()
    success = user is not None and user.check_password(password)

    _log_login_event(
        username_attempted=username,
        success=success,
        user_id=user.id if user else None,
    )

    if success:
        login_user(user)

        # Create the Session row — this is the real "start of a continuous
        # Zero Trust session," not just a login event. Everything from here
        # (mid-session risk re-evaluation, forced termination) hinges on
        # this row existing.
        new_session_id = generate_session_id()
        flask_session["app_session_id"] = new_session_id

        device_fp = get_device_fingerprint(request.headers.get("User-Agent", ""))
        ip = request.remote_addr or "unknown"

        login_event = LoginEvent.query.filter_by(
            user_id=user.id, success=True
        ).order_by(LoginEvent.id.desc()).first()
        # the row _log_login_event() just wrote, moments ago, in this same request

        login_event.session_id = new_session_id

        db.session.add(Session(
            session_id=new_session_id,
            user_id=user.id,
            login_event_id=login_event.id,
            started_at=datetime.utcnow(),
            start_ip=ip,
            current_ip=ip,
            start_device_fingerprint=device_fp,
            current_device_fingerprint=device_fp,
            is_active=True,
        ))
        db.session.commit()

        return jsonify({
            "message": "Login successful.",
            "user": {"id": user.id, "username": user.username, "role": user.role},
        }), 200

    return jsonify({"error": "Invalid username or password."}), 401


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