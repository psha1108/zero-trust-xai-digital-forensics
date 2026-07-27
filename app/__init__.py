from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from app.extensions import db, login_manager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

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

    db.init_app(app)
    login_manager.init_app(app)

    # Flask-Login's default behavior redirects unauthenticated users to an
    # HTML login page. That's meaningless for a JSON API — React needs a
    # proper 401 status with a JSON body instead, so it can react programmatically.
    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"error": "Authentication required"}), 401

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

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(resources_bp)

    return app
