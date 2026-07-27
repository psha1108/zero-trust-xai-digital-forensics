from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models import User, LoginEvent

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
    db.session.commit()
    return event


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not username or not email or not password:
        return jsonify({"error": "All fields are required."}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Username or email already exists."}), 409

    user = User(username=username, email=email)
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
        return jsonify({
            "message": "Login successful.",
            "user": {"id": user.id, "username": user.username, "role": user.role},
        }), 200

    return jsonify({"error": "Invalid username or password."}), 401


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
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