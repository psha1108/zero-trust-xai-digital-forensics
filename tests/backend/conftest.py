"""Isolated Flask/SQLAlchemy fixtures for backend tests."""

from __future__ import annotations

import pytest
from flask import Flask

from app.extensions import db

# Import models so SQLAlchemy metadata contains every application table.
from app import models as app_models  # noqa: F401


@pytest.fixture()
def database_app():
    """
    Provide an isolated in-memory SQLite application.

    This fixture deliberately does not call the production create_app()
    factory because the production configuration points to MySQL.
    """

    app = Flask("zero-trust-backend-tests")

    app.config.update(
        TESTING=True,
        SECRET_KEY="backend-test-only",
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)

    with app.app_context():
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()