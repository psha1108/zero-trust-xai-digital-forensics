"""Safety tests for the isolated backend database fixture."""

from __future__ import annotations

from app.extensions import db
from app.models import User


def test_backend_tests_use_isolated_sqlite(database_app) -> None:
    with database_app.app_context():
        database_url = str(db.engine.url)

        assert database_url.startswith("sqlite://")
        assert "mysql" not in database_url.lower()

        user = User(
            username="backend-fixture-user",
            email="backend-fixture@example.test",
            password_hash="test-only",
            role="employee",
        )

        db.session.add(user)
        db.session.commit()

        assert User.query.count() == 1

        stored = User.query.filter_by(
            username="backend-fixture-user"
        ).one()

        assert stored.role == "employee"