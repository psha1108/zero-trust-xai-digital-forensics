from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models import User, LoginEvent

auth_bp = Blueprint("auth", __name__)


def _log_login_event(username_attempted: str, success: bool, user_id: int | None) -> LoginEvent:
    """
    STEP 2 (Real-time log generation) lives here.
    Every single login attempt — successful or not — is written to the
    login_events table immediately. This function is the single source
    of truth for that table, so later (Step 4) feature_extraction.py
    only needs to know about this schema, not about auth logic.
    """
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


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already exists.", "danger")
            return redirect(url_for("auth.register"))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        success = user is not None and user.check_password(password)

        # Log the attempt BEFORE deciding the outcome — forensic logs must
        # capture failed attempts too, not just successful ones.
        _log_login_event(
            username_attempted=username,
            success=success,
            user_id=user.id if user else None,
        )

        if success:
            login_user(user)
            flash("Login successful.", "success")
            return redirect(url_for("dashboard.home"))
        else:
            flash("Invalid username or password.", "danger")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
