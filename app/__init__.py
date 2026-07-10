from flask import Flask

from config import Config
from app.extensions import db, login_manager


def create_app():
    """
    Application factory pattern. Using a factory (instead of a bare
    module-level `app = Flask(__name__)`) makes it possible to create
    multiple app instances later — one for running the server, one for
    tests, one for scripts that need app context (e.g. the synthetic
    log generator in Step 3) — all sharing the same configuration.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Import models here (not at top) so they register with db
    # only once the app + db are both initialized.
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    return app
