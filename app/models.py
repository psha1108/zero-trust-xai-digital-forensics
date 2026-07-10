from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    """
    Registered application user.

    UserMixin (from Flask-Login) supplies is_authenticated, is_active,
    is_anonymous, and get_id() so Flask-Login can manage sessions for us.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    login_events = db.relationship("LoginEvent", backref="user", lazy=True)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


class LoginEvent(db.Model):
    """
    One row per login attempt. This table is the raw data source for the
    entire ML pipeline (feature extraction reads from here) and for the
    forensics module (timeline reconstruction reads from here too).

    success        -> did the credentials check out
    risk_label     -> filled in LATER by the Random Forest (Step 6)
    anomaly_score  -> filled in LATER by the Isolation Forest (Step 5)
    cluster_id     -> filled in LATER by K-Means (Step 7)
    action_taken   -> filled in LATER by the policy engine (Step 10)
    These four columns are nullable now and populated once we build
    the ML layer — the table doesn't need to change shape later.
    """
    __tablename__ = "login_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    username_attempted = db.Column(db.String(80), nullable=False)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    device_info = db.Column(db.String(255), nullable=True)   # user-agent string
    success = db.Column(db.Boolean, nullable=False)
    session_duration_sec = db.Column(db.Integer, nullable=True)

    anomaly_score = db.Column(db.Float, nullable=True)
    risk_label = db.Column(db.String(10), nullable=True)      # Low / Medium / High
    cluster_id = db.Column(db.Integer, nullable=True)
    action_taken = db.Column(db.String(10), nullable=True)    # Allow / OTP / Block


class EvidenceLog(db.Model):
    """
    Tamper-evident forensic record. Each row is hash-chained to the
    previous row (like a mini blockchain) so any retroactive edit to
    a past record is detectable — critical for a digital forensics module.
    """
    __tablename__ = "evidence_logs"

    id = db.Column(db.Integer, primary_key=True)
    login_event_id = db.Column(db.Integer, db.ForeignKey("login_events.id"), nullable=False)
    details = db.Column(db.Text, nullable=False)   # JSON-serialized event snapshot
    record_hash = db.Column(db.String(64), nullable=False)      # SHA-256 of this record
    previous_hash = db.Column(db.String(64), nullable=True)     # SHA-256 of the prior record
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
