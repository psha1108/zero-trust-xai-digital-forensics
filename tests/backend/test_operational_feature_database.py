"""Database contract tests for live operational ML feature construction."""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from app.extensions import db
from app.models import AccessEvent, LoginEvent, Session, User
from app.services.operational_features import (
    build_operational_feature_record_from_database,
)
from ml.classification.preprocessing import (
    MODEL_FEATURE_COLUMNS,
    select_random_forest_features,
)


def test_database_builder_uses_exact_session_and_event_history(
    database_app,
) -> None:
    with database_app.app_context():
        login_time = datetime(2026, 8, 31, 10, 0, 0)

        user = User(
            username="employee-one",
            email="employee-one@example.test",
            password_hash="test-only",
            role="employee",
        )

        other_user = User(
            username="other-user",
            email="other-user@example.test",
            password_hash="test-only",
            role="admin",
        )

        db.session.add_all([user, other_user])
        db.session.flush()

        prior_success = LoginEvent(
            user_id=user.id,
            username_attempted=user.username,
            timestamp=login_time - timedelta(minutes=20),
            ip_address="10.0.0.2",
            device_info="Mozilla/5.0 Windows Firefox/139.0",
            success=True,
        )

        prior_failure_one = LoginEvent(
            user_id=user.id,
            username_attempted=user.username,
            timestamp=login_time - timedelta(minutes=3),
            ip_address="10.0.0.5",
            device_info="Mozilla/5.0 Windows Chrome/140.0",
            success=False,
        )

        prior_failure_two = LoginEvent(
            user_id=user.id,
            username_attempted=user.username,
            timestamp=login_time - timedelta(minutes=2),
            ip_address="10.0.0.5",
            device_info="Mozilla/5.0 Windows Chrome/140.0",
            success=False,
        )

        unrelated_failure = LoginEvent(
            user_id=other_user.id,
            username_attempted=other_user.username,
            timestamp=login_time - timedelta(minutes=1),
            ip_address="203.0.113.50",
            device_info="Mozilla/5.0 Linux Firefox/139.0",
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
                prior_failure_one,
                prior_failure_two,
                unrelated_failure,
                current_login,
            ]
        )
        db.session.flush()

        session = Session(
            session_id="session-under-test",
            user_id=user.id,
            login_event_id=current_login.id,
            started_at=login_time,
            start_ip="10.0.0.5",
            current_ip="10.0.0.5",
            start_device_fingerprint="chrome-windows",
            current_device_fingerprint="chrome-windows",
            is_active=True,
        )

        unrelated_session = Session(
            session_id="unrelated-session",
            user_id=other_user.id,
            login_event_id=unrelated_failure.id,
            started_at=login_time,
            start_ip="203.0.113.50",
            current_ip="203.0.113.50",
            start_device_fingerprint="firefox-linux",
            current_device_fingerprint="firefox-linux",
            is_active=True,
        )

        db.session.add_all([session, unrelated_session])
        db.session.flush()

        access_one = AccessEvent(
            user_id=user.id,
            session_id=session.session_id,
            resource="normal_page",
            resource_sensitivity="low",
            timestamp=login_time + timedelta(minutes=4),
            ip_address="10.0.0.5",
            privilege_mismatch=False,
            ip_changed=False,
            device_changed=False,
        )

        access_two = AccessEvent(
            user_id=user.id,
            session_id=session.session_id,
            resource="confidential_page",
            resource_sensitivity="critical",
            timestamp=login_time + timedelta(minutes=5),
            ip_address="10.0.0.5",
            privilege_mismatch=False,
            ip_changed=False,
            device_changed=True,
        )

        access_three = AccessEvent(
            user_id=user.id,
            session_id=session.session_id,
            resource="hr_page",
            resource_sensitivity="medium",
            timestamp=login_time + timedelta(minutes=8),
            ip_address="10.0.0.5",
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
            privilege_mismatch=True,
            ip_changed=True,
            device_changed=False,
        )

        unrelated_access = AccessEvent(
            user_id=other_user.id,
            session_id=unrelated_session.session_id,
            resource="admin_page",
            resource_sensitivity="critical",
            timestamp=login_time + timedelta(minutes=9),
            ip_address="203.0.113.50",
            privilege_mismatch=True,
            ip_changed=True,
            device_changed=True,
        )

        db.session.add_all(
            [
                access_one,
                access_two,
                access_three,
                current_access,
                unrelated_access,
            ]
        )
        db.session.commit()

        record = build_operational_feature_record_from_database(
            session_id=session.session_id,
            access_event_id=current_access.id,
        )

        assert list(record) == MODEL_FEATURE_COLUMNS

        assert record == {
            "role": "employee",
            "login_hour": 10,
            "is_working_hour": 1,
            "failed_attempt_count": 2,
            "is_new_ip": 1,
            "is_new_device": 1,
            "is_unusual_time": 0,
            "session_duration_minutes": 10.0,
            "resource_sensitivity_score": 3,
            "access_count_5min": 3,
            "unauthorized_access_attempt": 1,
            "ip_changed_during_session": 1,
            "device_changed_during_session": 1,
            "sensitive_resource_access_count": 2,
        }

        selected = select_random_forest_features(
            pd.DataFrame([record])
        )

        assert selected.shape == (1, 14)
        assert selected.columns.tolist() == MODEL_FEATURE_COLUMNS


def test_database_builder_excludes_access_events_after_current_event(
    database_app,
) -> None:
    with database_app.app_context():
        login_time = datetime(2026, 8, 31, 9, 0, 0)

        user = User(
            username="employee-two",
            email="employee-two@example.test",
            password_hash="test-only",
            role="employee",
        )

        db.session.add(user)
        db.session.flush()

        login_event = LoginEvent(
            user_id=user.id,
            username_attempted=user.username,
            timestamp=login_time,
            ip_address="10.0.0.10",
            device_info="Mozilla/5.0 Windows Chrome/140.0",
            success=True,
        )

        db.session.add(login_event)
        db.session.flush()

        session = Session(
            session_id="ordered-session",
            user_id=user.id,
            login_event_id=login_event.id,
            started_at=login_time,
            start_ip="10.0.0.10",
            current_ip="10.0.0.10",
            start_device_fingerprint="chrome-windows",
            current_device_fingerprint="chrome-windows",
            is_active=True,
        )

        db.session.add(session)
        db.session.flush()

        current_access = AccessEvent(
            user_id=user.id,
            session_id=session.session_id,
            resource="normal_page",
            resource_sensitivity="low",
            timestamp=login_time + timedelta(minutes=1),
            ip_address="10.0.0.10",
            privilege_mismatch=False,
            ip_changed=False,
            device_changed=False,
        )

        future_access = AccessEvent(
            user_id=user.id,
            session_id=session.session_id,
            resource="confidential_page",
            resource_sensitivity="critical",
            timestamp=login_time + timedelta(minutes=2),
            ip_address="10.0.0.20",
            privilege_mismatch=True,
            ip_changed=True,
            device_changed=True,
        )

        db.session.add_all([current_access, future_access])
        db.session.commit()

        record = build_operational_feature_record_from_database(
            session_id=session.session_id,
            access_event_id=current_access.id,
        )

        assert record["access_count_5min"] == 1
        assert record["unauthorized_access_attempt"] == 0
        assert record["ip_changed_during_session"] == 0
        assert record["device_changed_during_session"] == 0
        assert record["sensitive_resource_access_count"] == 0