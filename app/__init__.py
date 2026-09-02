from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from app.extensions import db, login_manager


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    # Allow the React dev server to call this API with cookies included.
    # Add both common React dev ports (CRA=3000, Vite=5173) so either works.
    CORS(app, supports_credentials=True, origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ])

    # Cross-port localhost requests are still "same-site" to browsers, so
    # Lax works for local dev without needing HTTPS. In production, this
    # should become 'None' + SESSION_COOKIE_SECURE=True, served over HTTPS.
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    import os
    if os.environ.get("TRUST_REVERSE_PROXY", "false").lower() == "true":
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    db.init_app(app)
    login_manager.init_app(app)

    # Flask-Login's default behavior redirects unauthenticated users to an
    # HTML login page. That's meaningless for a JSON API — React needs a
    # proper 401 status with a JSON body instead, so it can react programmatically.
    @app.before_request
    def enforce_active_session():
        """
        The actual enforcement mechanism for Adaptive Access Control.
        Flask-Login's cookie alone doesn't know if we've decided this
        session should be terminated — this check does. Runs before
        every request; if the session has been marked inactive (by
        logout, or in future by the policy engine), the request is
        rejected here, regardless of cookie validity.
        """
        from flask_login import current_user
        from flask import session as flask_session, request

        if not current_user.is_authenticated:
            return  # let login/register/unauthenticated requests through normally

        session_id = flask_session.get("app_session_id")
        if not session_id:
            return jsonify({"error": "Session invalid. Please log in again."}), 401

        from app.models import Session
        session_row = Session.query.filter_by(session_id=session_id).first()

        if not session_row or not session_row.is_active:
            return jsonify({"error": "Session has been terminated. Please log in again."}), 401

    # Import models here (not at top) so they register with db
    # only once the app + db are both initialized.
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.resources import resources_bp
    from app.routes.forensics import forensics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(forensics_bp)

    return app
