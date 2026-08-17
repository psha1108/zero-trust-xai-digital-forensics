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
    session_duration_sec = db.Column(db.Integer, nullable=True)  # populated when the session ends (feature/session-lifecycle)
    session_id = db.Column(db.String(64), nullable=True)  # links a successful login to its Session row

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

class Session(db.Model):
    """
    One row per active or past login session. This is the actual
    enforcement mechanism for Adaptive Access Control: is_active=False
    is what genuinely terminates a session, independent of whether the
    browser's Flask-Login cookie is still technically valid.

    Also the anchor table for session-time ML features (join against
    access_events on session_id) and for forensic timeline reconstruction.
    """
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    login_event_id = db.Column(db.Integer, db.ForeignKey("login_events.id"), nullable=False)

    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)
    end_reason = db.Column(db.String(20), nullable=True)  # logout / timeout / blocked / terminated

    start_ip = db.Column(db.String(45), nullable=False)
    current_ip = db.Column(db.String(45), nullable=False)
    start_device_fingerprint = db.Column(db.String(100), nullable=False)
    current_device_fingerprint = db.Column(db.String(100), nullable=False)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    current_risk_score = db.Column(db.Float, nullable=True)
    current_risk_label = db.Column(db.String(10), nullable=True)

    user = db.relationship("User", backref="sessions")
    login_event = db.relationship("LoginEvent", backref="session")

class AccessEvent(db.Model):
    """
    Logs every request to a protected resource DURING an active session —
    not just the login itself. This is what makes the system continuous
    Zero Trust rather than one-time login screening: risk gets recalculated
    every time this table gets a new row.
    """
    __tablename__ = "access_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_id = db.Column(db.String(64), nullable=False)

    resource = db.Column(db.String(100), nullable=False)
    resource_sensitivity = db.Column(db.String(10), nullable=False)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    request_count = db.Column(db.Integer, default=1)

    ip_address = db.Column(db.String(45), nullable=False)
    device_id = db.Column(db.String(255), nullable=True)             # raw User-Agent, kept for audit
    device_fingerprint = db.Column(db.String(100), nullable=True)    # parsed, for ML comparisons
    privilege_mismatch = db.Column(db.Boolean, default=False, nullable=False)
    ip_changed = db.Column(db.Boolean, default=False, nullable=False)        # True if IP differs from session start/last-known
    device_changed = db.Column(db.Boolean, default=False, nullable=False)    # True if device fingerprint differs

    decision = db.Column(db.String(10), nullable=True)
    risk_score = db.Column(db.Float, nullable=True)

    user = db.relationship("User", backref="access_events")
