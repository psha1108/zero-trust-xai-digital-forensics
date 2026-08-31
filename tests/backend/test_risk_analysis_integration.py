"""End-to-end backend integration test using the official RF and SHAP stack."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models import AccessEvent, LoginEvent, Session, User
from app.services.risk_analysis import analyze_operational_access
from ml.classification.preprocessing import MODEL_FEATURE_COLUMNS


def test_database_to_random_forest_to_shap_pipeline(
    database_app,
) -> None:
    """
    Verify the real persisted-event -> features -> RF -> SHAP chain.

    The database is isolated SQLite, while Random Forest and SHAP use the
    official production artifact already frozen by the ML pipeline.
    """

    with database_app.app_context():
        login_time = datetime(2026, 8, 31, 10, 0, 0)

        user = User(
            username="integration-user",
            email="integration-user@example.test",
            password_hash="test-only",
            role="employee",
        )

        db.session.add(user)
        db.session.flush()

        prior_success = LoginEvent(
            user_id=user.id,
            username_attempted=user.username,
            timestamp=login_time - timedelta(hours=2),
            ip_address="10.0.0.2",
            device_info="Mozilla/5.0 Windows Firefox/139.0",
            success=True,
        )

        prior_failure = LoginEvent(
            user_id=user.id,
            username_attempted=user.username,
            timestamp=login_time - timedelta(minutes=2),
            ip_address="10.0.0.5",
            device_info="Mozilla/5.0 Windows Chrome/140.0",
            success=False,
        )

        current_login = LoginEvent(
            user_id=user.id,
            username_attempted=user.username,
            timestamp=login_time,
            ip_address="10.0.0.5",
            device_info="Mozilla/5.0 Windows Chrome/140.0",
            success=True,
        )

        db.session.add_all(
            [
                prior_success,
                prior_failure,
                current_login,
            ]
        )
        db.session.flush()

        session = Session(
            session_id="real-analysis-session",
            user_id=user.id,
            login_event_id=current_login.id,
            started_at=login_time,
            start_ip="10.0.0.5",
            current_ip="10.0.0.5",
            start_device_fingerprint="chrome-windows",
            current_device_fingerprint="chrome-windows",
            is_active=True,
        )

        db.session.add(session)
        db.session.flush()

        earlier_access = AccessEvent(
            user_id=user.id,
            session_id=session.session_id,
            resource="normal_page",
            resource_sensitivity="low",
            timestamp=login_time + timedelta(minutes=7),
            ip_address="10.0.0.5",
            device_fingerprint="chrome-windows",
            privilege_mismatch=False,
            ip_changed=False,
            device_changed=False,
        )

        current_access = AccessEvent(
            user_id=user.id,
            session_id=session.session_id,
            resource="finance_page",
            resource_sensitivity="high",
            timestamp=login_time + timedelta(minutes=10),
            ip_address="10.0.0.8",
            device_fingerprint="chrome-windows",
            privilege_mismatch=True,
            ip_changed=True,
            device_changed=False,
        )

        db.session.add_all(
            [
                earlier_access,
                current_access,
            ]
        )
        db.session.commit()

        result = analyze_operational_access(
            session_id=session.session_id,
            access_event_id=current_access.id,
        )

        assert list(result["features"]) == MODEL_FEATURE_COLUMNS
        assert len(result["features"]) == 14

        prediction = result["prediction"]
        explanation = result["explanation"]

        assert prediction["predicted_risk"] in {
            "low",
            "medium",
            "high",
        }

        probabilities = [
            prediction["probability_low"],
            prediction["probability_medium"],
            prediction["probability_high"],
        ]

        assert sum(probabilities) == pytest.approx(
            1.0,
            abs=1e-12,
        )

        assert explanation["prediction"] == (
            prediction["predicted_risk"]
        )

        assert explanation["class_order"] == [
            "high",
            "low",
            "medium",
        ]

        assert explanation["model_probability"] == pytest.approx(
            prediction[
                f"probability_{prediction['predicted_risk']}"
            ],
            abs=1e-12,
        )

        assert explanation["additivity"]["is_additive"] is True
        assert explanation["additivity"]["additivity_error"] <= 1e-6

        # Flask will ultimately return this structure as JSON.
        serialized = json.dumps(result)

        assert isinstance(serialized, str)
        assert serialized