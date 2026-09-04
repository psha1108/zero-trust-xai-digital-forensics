"""Security contract for Zero Trust OTP step-up authentication.

OTP is a separate security service. It must not be implemented inside
the ML inference layer or the pure Zero Trust decision engine.

Frozen behavior:

- OTP codes contain exactly six decimal digits.
- OTP challenge lifetime is 300 seconds.
- A pending unexpired challenge is reused instead of duplicated.
- Only a hash of the OTP is persisted.
- Maximum failed verification attempts is five.
- Five failed attempts lock the challenge.
- Successful verification creates a 300-second step-up grant.
- A grant is scoped to the same application session and resource.
- Expired OTP challenges cannot be verified.
- A challenge may only be created for the matching active user session.

The delivery transport is deliberately abstracted. Tests replace the
delivery function with an in-memory capture. A later integration step
will connect this service to the Flask HTTP endpoints.
"""

from __future__ import annotations

import importlib
from datetime import datetime, timedelta

import pytest

from app.extensions import db
from app.models import LoginEvent, Session, User


TEST_OTP = "123456"


def _otp_module():
    return importlib.import_module(
        "app.services.otp_service"
    )


def _otp_model():
    models = importlib.import_module(
        "app.models"
    )

    return getattr(
        models,
        "OtpChallenge",
    )


def _prepare_database(
    database_app,
) -> None:
    # otp_service imports/registers OtpChallenge before this call.
    with database_app.app_context():
        db.create_all()


def _seed_active_session(
    database_app,
    *,
    suffix: str,
) -> tuple[str, int, str]:
    with database_app.app_context():
        user = User(
            username=f"otp-{suffix}",
            email=f"otp-{suffix}@example.test",
            password_hash="test-only",
            role="employee",
        )

        db.session.add(user)
        db.session.flush()

        login_event = LoginEvent(
            user_id=user.id,
            username_attempted=user.username,
            timestamp=datetime(
                2026,
                9,
                2,
                15,
                0,
                0,
            ),
            ip_address="10.0.0.5",
            device_info="otp-test-device",
            success=True,
        )

        db.session.add(login_event)
        db.session.flush()

        session_id = (
            f"otp-session-{suffix}"
        )

        login_event.session_id = (
            session_id
        )

        session_row = Session(
            session_id=session_id,
            user_id=user.id,
            login_event_id=login_event.id,
            started_at=datetime(
                2026,
                9,
                2,
                15,
                0,
                0,
            ),
            start_ip="10.0.0.5",
            current_ip="10.0.0.5",
            start_device_fingerprint="device-a",
            current_device_fingerprint="device-a",
            is_active=True,
        )

        db.session.add(session_row)
        db.session.commit()

        return (
            session_id,
            user.id,
            user.email,
        )


def _install_test_delivery(
    monkeypatch,
    module,
) -> list[tuple[str, str]]:
    delivered = []

    monkeypatch.setattr(
        module,
        "_generate_otp_code",
        lambda: TEST_OTP,
    )

    def fake_delivery(
        *,
        target: str,
        code: str,
    ) -> None:
        delivered.append(
            (
                target,
                code,
            )
        )

    monkeypatch.setattr(
        module,
        "_deliver_otp_code",
        fake_delivery,
    )

    return delivered


def test_create_challenge_hashes_six_digit_otp(
    database_app,
    monkeypatch,
) -> None:
    module = _otp_module()

    _prepare_database(
        database_app
    )

    (
        session_id,
        user_id,
        email,
    ) = _seed_active_session(
        database_app,
        suffix="create",
    )

    delivered = _install_test_delivery(
        monkeypatch,
        module,
    )

    with database_app.app_context():
        result = module.create_otp_challenge(
            session_id=session_id,
            user_id=user_id,
            resource="finance_page",
            delivery_target=email,
        )

        assert result == {
            "status": "pending",
            "expires_in_seconds": 300,
        }

        assert delivered == [
            (
                email,
                TEST_OTP,
            )
        ]

        OtpChallenge = _otp_model()

        rows = OtpChallenge.query.all()

        assert len(rows) == 1

        challenge = rows[0]

        assert challenge.session_id == session_id
        assert challenge.user_id == user_id
        assert challenge.resource == "finance_page"

        assert challenge.otp_hash
        assert challenge.otp_hash != TEST_OTP

        assert challenge.failed_attempts == 0
        assert challenge.max_attempts == 5
        assert challenge.verified_at is None

        lifetime = (
            challenge.expires_at
            - challenge.created_at
        ).total_seconds()

        assert lifetime == pytest.approx(
            300.0,
            abs=1.0,
        )

        column_names = {
            column.name
            for column in OtpChallenge.__table__.columns
        }

        assert "otp_hash" in column_names
        assert "otp_code" not in column_names
        assert "code" not in column_names


def test_pending_challenge_is_reused_not_duplicated(
    database_app,
    monkeypatch,
) -> None:
    module = _otp_module()

    _prepare_database(
        database_app
    )

    (
        session_id,
        user_id,
        email,
    ) = _seed_active_session(
        database_app,
        suffix="reuse",
    )

    delivered = _install_test_delivery(
        monkeypatch,
        module,
    )

    with database_app.app_context():
        first = module.create_otp_challenge(
            session_id=session_id,
            user_id=user_id,
            resource="finance_page",
            delivery_target=email,
        )

        second = module.create_otp_challenge(
            session_id=session_id,
            user_id=user_id,
            resource="finance_page",
            delivery_target=email,
        )

        assert first == {
            "status": "pending",
            "expires_in_seconds": 300,
        }

        assert second == {
            "status": "pending",
            "expires_in_seconds": 300,
        }

        OtpChallenge = _otp_model()

        assert OtpChallenge.query.count() == 1

        # Reusing a pending challenge must not silently rotate
        # the OTP or send a second code.
        assert delivered == [
            (
                email,
                TEST_OTP,
            )
        ]


def test_correct_otp_creates_resource_scoped_step_up_grant(
    database_app,
    monkeypatch,
) -> None:
    module = _otp_module()

    _prepare_database(
        database_app
    )

    (
        session_id,
        user_id,
        email,
    ) = _seed_active_session(
        database_app,
        suffix="verify",
    )

    _install_test_delivery(
        monkeypatch,
        module,
    )

    with database_app.app_context():
        module.create_otp_challenge(
            session_id=session_id,
            user_id=user_id,
            resource="finance_page",
            delivery_target=email,
        )

        result = module.verify_otp_code(
            session_id=session_id,
            user_id=user_id,
            otp_code=TEST_OTP,
        )

        assert result == {
            "verified": True,
            "status": "verified",
            "attempts_remaining": 5,
        }

        OtpChallenge = _otp_model()

        challenge = (
            OtpChallenge.query
            .filter_by(
                session_id=session_id,
                user_id=user_id,
                resource="finance_page",
            )
            .one()
        )

        assert challenge.verified_at is not None

        assert module.has_valid_otp_grant(
            session_id=session_id,
            user_id=user_id,
            resource="finance_page",
        ) is True

        # Step-up approval is not a universal session bypass.
        assert module.has_valid_otp_grant(
            session_id=session_id,
            user_id=user_id,
            resource="admin_page",
        ) is False


def test_wrong_otp_increments_attempts_without_grant(
    database_app,
    monkeypatch,
) -> None:
    module = _otp_module()

    _prepare_database(
        database_app
    )

    (
        session_id,
        user_id,
        email,
    ) = _seed_active_session(
        database_app,
        suffix="wrong",
    )

    _install_test_delivery(
        monkeypatch,
        module,
    )

    with database_app.app_context():
        module.create_otp_challenge(
            session_id=session_id,
            user_id=user_id,
            resource="finance_page",
            delivery_target=email,
        )

        result = module.verify_otp_code(
            session_id=session_id,
            user_id=user_id,
            otp_code="000000",
        )

        assert result == {
            "verified": False,
            "status": "invalid",
            "attempts_remaining": 4,
        }

        OtpChallenge = _otp_model()

        challenge = OtpChallenge.query.one()

        assert challenge.failed_attempts == 1
        assert challenge.verified_at is None

        assert module.has_valid_otp_grant(
            session_id=session_id,
            user_id=user_id,
            resource="finance_page",
        ) is False


def test_fifth_wrong_attempt_locks_challenge(
    database_app,
    monkeypatch,
) -> None:
    module = _otp_module()

    _prepare_database(
        database_app
    )

    (
        session_id,
        user_id,
        email,
    ) = _seed_active_session(
        database_app,
        suffix="locked",
    )

    _install_test_delivery(
        monkeypatch,
        module,
    )

    with database_app.app_context():
        module.create_otp_challenge(
            session_id=session_id,
            user_id=user_id,
            resource="finance_page",
            delivery_target=email,
        )

        for remaining in (
            4,
            3,
            2,
            1,
        ):
            result = module.verify_otp_code(
                session_id=session_id,
                user_id=user_id,
                otp_code="000000",
            )

            assert result == {
                "verified": False,
                "status": "invalid",
                "attempts_remaining": remaining,
            }

        fifth = module.verify_otp_code(
            session_id=session_id,
            user_id=user_id,
            otp_code="000000",
        )

        assert fifth == {
            "verified": False,
            "status": "locked",
            "attempts_remaining": 0,
        }

        correct_after_lock = (
            module.verify_otp_code(
                session_id=session_id,
                user_id=user_id,
                otp_code=TEST_OTP,
            )
        )

        assert correct_after_lock == {
            "verified": False,
            "status": "locked",
            "attempts_remaining": 0,
        }

        OtpChallenge = _otp_model()

        challenge = OtpChallenge.query.one()

        assert challenge.failed_attempts == 5
        assert challenge.verified_at is None

        assert module.has_valid_otp_grant(
            session_id=session_id,
            user_id=user_id,
            resource="finance_page",
        ) is False


def test_expired_challenge_cannot_be_verified(
    database_app,
    monkeypatch,
) -> None:
    module = _otp_module()

    _prepare_database(
        database_app
    )

    (
        session_id,
        user_id,
        email,
    ) = _seed_active_session(
        database_app,
        suffix="expired",
    )

    _install_test_delivery(
        monkeypatch,
        module,
    )

    with database_app.app_context():
        module.create_otp_challenge(
            session_id=session_id,
            user_id=user_id,
            resource="finance_page",
            delivery_target=email,
        )

        OtpChallenge = _otp_model()

        challenge = OtpChallenge.query.one()

        challenge.expires_at = (
            datetime.utcnow()
            - timedelta(seconds=1)
        )

        db.session.commit()

        result = module.verify_otp_code(
            session_id=session_id,
            user_id=user_id,
            otp_code=TEST_OTP,
        )

        assert result == {
            "verified": False,
            "status": "expired",
            "attempts_remaining": 0,
        }

        assert module.has_valid_otp_grant(
            session_id=session_id,
            user_id=user_id,
            resource="finance_page",
        ) is False


def test_verified_step_up_grant_expires_after_five_minutes(
    database_app,
    monkeypatch,
) -> None:
    module = _otp_module()

    _prepare_database(
        database_app
    )

    (
        session_id,
        user_id,
        email,
    ) = _seed_active_session(
        database_app,
        suffix="grant-expired",
    )

    _install_test_delivery(
        monkeypatch,
        module,
    )

    with database_app.app_context():
        module.create_otp_challenge(
            session_id=session_id,
            user_id=user_id,
            resource="finance_page",
            delivery_target=email,
        )

        module.verify_otp_code(
            session_id=session_id,
            user_id=user_id,
            otp_code=TEST_OTP,
        )

        OtpChallenge = _otp_model()

        challenge = OtpChallenge.query.one()

        challenge.verified_at = (
            datetime.utcnow()
            - timedelta(seconds=301)
        )

        db.session.commit()

        assert module.has_valid_otp_grant(
            session_id=session_id,
            user_id=user_id,
            resource="finance_page",
        ) is False


def test_challenge_rejects_mismatched_user_session(
    database_app,
    monkeypatch,
) -> None:
    module = _otp_module()

    _prepare_database(
        database_app
    )

    (
        session_id,
        user_id,
        email,
    ) = _seed_active_session(
        database_app,
        suffix="mismatch",
    )

    _install_test_delivery(
        monkeypatch,
        module,
    )

    with database_app.app_context():
        with pytest.raises(
            ValueError,
            match="session",
        ):
            module.create_otp_challenge(
                session_id=session_id,
                user_id=user_id + 999,
                resource="finance_page",
                delivery_target=email,
            )

        OtpChallenge = _otp_model()

        assert OtpChallenge.query.count() == 0
