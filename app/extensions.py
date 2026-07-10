from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# These are instantiated here (without an app) and bound to the app
# later inside create_app(). This avoids circular imports between
# app/__init__.py and app/models.py.
db = SQLAlchemy()
login_manager = LoginManager()
