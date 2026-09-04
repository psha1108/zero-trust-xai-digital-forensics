"""HTTP contract for Zero Trust OTP step-up authentication.

The standalone OTP service already exists. These tests freeze how Flask
must integrate that service with protected-resource requests.

Required flow:

1. A protected request whose policy action is OTP automatically creates
   or reuses a resource-scoped OTP challenge.
2. The protected resource is not returned yet; HTTP 401 remains the
   existing OTP hand-off contract.
3. POST /api/auth/otp/verify verifies the active browser session's OTP.
4. A successful verification establishes the already-defined five-minute
   session + user + resource grant.
5. Retrying the same protected resource still runs ML/policy evaluation,
   but an OTP policy action is satisfied by that valid grant.
6. A grant for one resource cannot authorize another resource.
7. Malformed OTP input is rejected without consuming an attempt.

The OTP itself must never be returned by the API.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import OtpChallenge, User
from app.routes import resources
from app.services import otp_service
from config import Config


TEST_OTP = "123456"


def _otp_analysis() -> dict:
    return {
        "prediction": {
            "predicted_risk": "medium",
            "probability_low": 0.10,
            "probability_medium": 0.70,
            "probability_high": 0.20,
        },
        "anomaly_detection": {
            "anomaly_score": 0.40,
            "anomaly_threshold": 0.5532259181941123,
            "threshold_margin": (
                0.40
                - 0.5532259181941123
            ),
            "is_anomaly": False,
        },
        "behavioral_cluster": {
            "cluster_id": 1,
            "archetype_name": (
                "Routine Behavioral Activity"
            ),
        },
        "explanation": {
            "prediction": "medium",
        },
    }


def _authenticated_app(
    monkeypatch,
    *,
    suffix: str,
):
    monkeypatch.setattr(
        Config,
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:///:memory:",
    )

    monkeypatch.setattr(
        Config,
        "TESTING",
        True,
        raising=False,
    )

    monkeypatch.setattr(
        Config,
        "SECRET_KEY",
        "otp-http-contract-test-key",
    )

    app = create_app()

    with app.app_context():
        db.create_all()

        user = User(
            username=f"otp-http-{suffix}",
            email=f"otp-http-{suffix}@example.test",
            role="employee",
        )

        user.set_password(
            "StrongPass1!"
        )

        db.session.add(user)
        db.session.commit()

        user_id = user.id
        email = user.email

    analysis = _otp_analysis()

    def fake_analysis(
        *,
        session_id,
        access_event_id,
    ):
        assert isinstance(
            session_id,
            str,
        )

        assert isinstance(
            access_event_id,
            int,
        )

        return analysis

    monkeypatch.setattr(
        resources,
        "analyze_operational_access",
        fake_analysis,
    )

    delivered = []

    monkeypatch.setattr(
        otp_service,
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
        otp_service,
        "_deliver_otp_code",
        fake_delivery,
    )

    client = app.test_client()

    response = client.post(
        "/api/auth/login",
        json={
            "username": f"otp-http-{suffix}",
            "password": "StrongPass1!",
        },
        headers={
            "User-Agent": "OtpContractBrowser/1.0",
        },
    )

    assert response.status_code == 200

    with client.session_transaction() as flask_session:
        session_id = flask_session[
            "app_session_id"
        ]

    return (
        app,
        client,
        user_id,
        session_id,
        email,
        delivered,
    )


def _create_pending_challenge(
    app,
    *,
    session_id: str,
    user_id: int,
    email: str,
    resource: str = "finance_page",
) -> None:
    with app.app_context():
        otp_service.create_otp_challenge(
            session_id=session_id,
            user_id=user_id,
            resource=resource,
            delivery_target=email,
        )


def _cleanup(
    app,
) -> None:
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_otp_policy_automatically_creates_challenge(
    monkeypatch,
) -> None:
    (
        app,
        client,
        user_id,
        session_id,
        email,
        delivered,
    ) = _authenticated_app(
        monkeypatch,
        suffix="challenge",
    )

    try:
        response = client.get(
            "/api/resources/finance",
            headers={
                "User-Agent": "OtpContractBrowser/1.0",
            },
        )

        assert response.status_code == 401

        # Preserve the already-frozen OTP HTTP hand-off.
        assert response.get_json() == {
            "error": "OTP verification required.",
            "policy_action": "OTP",
            "requires_otp": True,
        }

        with app.app_context():
            challenge = (
                OtpChallenge.query
                .filter_by(
                    session_id=session_id,
                    user_id=user_id,
                    resource="finance_page",
                )
                .one()
            )

            assert challenge.otp_hash
            assert challenge.otp_hash != TEST_OTP
            assert challenge.verified_at is None

        assert delivered == [
            (
                email,
                TEST_OTP,
            )
        ]

        # The API hand-off itself must not expose the OTP.
        assert TEST_OTP not in response.get_data(
            as_text=True
        )

    finally:
        _cleanup(app)


def test_correct_http_otp_verification_creates_grant(
    monkeypatch,
) -> None:
    (
        app,
        client,
        user_id,
        session_id,
        email,
        _delivered,
    ) = _authenticated_app(
        monkeypatch,
        suffix="verify",
    )

    try:
        _create_pending_challenge(
            app,
            session_id=session_id,
            user_id=user_id,
            email=email,
        )

        response = client.post(
            "/api/auth/otp/verify",
            json={
                "otp_code": TEST_OTP,
            },
        )

        assert response.status_code == 200

        assert response.get_json() == {
            "message": "OTP verified.",
            "verified": True,
        }

        with app.app_context():
            assert otp_service.has_valid_otp_grant(
                session_id=session_id,
                user_id=user_id,
                resource="finance_page",
            ) is True

    finally:
        _cleanup(app)


def test_wrong_http_otp_returns_attempts_remaining(
    monkeypatch,
) -> None:
    (
        app,
        client,
        user_id,
        session_id,
        email,
        _delivered,
    ) = _authenticated_app(
        monkeypatch,
        suffix="wrong",
    )

    try:
        _create_pending_challenge(
            app,
            session_id=session_id,
            user_id=user_id,
            email=email,
        )

        response = client.post(
            "/api/auth/otp/verify",
            json={
                "otp_code": "000000",
            },
        )

        assert response.status_code == 400

        assert response.get_json() == {
            "error": "Invalid OTP.",
            "verified": False,
            "attempts_remaining": 4,
        }

        with app.app_context():
            challenge = (
                OtpChallenge.query.one()
            )

            assert challenge.failed_attempts == 1
            assert challenge.verified_at is None

    finally:
        _cleanup(app)


def test_malformed_http_otp_does_not_consume_attempt(
    monkeypatch,
) -> None:
    (
        app,
        client,
        user_id,
        session_id,
        email,
        _delivered,
    ) = _authenticated_app(
        monkeypatch,
        suffix="malformed",
    )

    try:
        _create_pending_challenge(
            app,
            session_id=session_id,
            user_id=user_id,
            email=email,
        )

        response = client.post(
            "/api/auth/otp/verify",
            json={
                "otp_code": "12ab",
            },
        )

        assert response.status_code == 400

        assert response.get_json() == {
            "error": "A 6-digit OTP is required.",
        }

        with app.app_context():
            challenge = (
                OtpChallenge.query.one()
            )

            assert challenge.failed_attempts == 0
            assert challenge.verified_at is None

    finally:
        _cleanup(app)


def test_http_fifth_wrong_attempt_returns_locked(
    monkeypatch,
) -> None:
    (
        app,
        client,
        user_id,
        session_id,
        email,
        _delivered,
    ) = _authenticated_app(
        monkeypatch,
        suffix="locked",
    )

    try:
        _create_pending_challenge(
            app,
            session_id=session_id,
            user_id=user_id,
            email=email,
        )

        with app.app_context():
            for _ in range(4):
                result = otp_service.verify_otp_code(
                    session_id=session_id,
                    user_id=user_id,
                    otp_code="000000",
                )

                assert result["status"] == "invalid"

        response = client.post(
            "/api/auth/otp/verify",
            json={
                "otp_code": "000000",
            },
        )

        assert response.status_code == 423

        assert response.get_json() == {
            "error": "OTP challenge locked.",
            "verified": False,
            "attempts_remaining": 0,
        }

    finally:
        _cleanup(app)


def test_http_expired_otp_returns_gone(
    monkeypatch,
) -> None:
    (
        app,
        client,
        user_id,
        session_id,
        email,
        _delivered,
    ) = _authenticated_app(
        monkeypatch,
        suffix="expired",
    )

    try:
        _create_pending_challenge(
            app,
            session_id=session_id,
            user_id=user_id,
            email=email,
        )

        with app.app_context():
            challenge = (
                OtpChallenge.query.one()
            )

            challenge.expires_at = (
                datetime.utcnow()
                - timedelta(seconds=1)
            )

            db.session.commit()

        response = client.post(
            "/api/auth/otp/verify",
            json={
                "otp_code": TEST_OTP,
            },
        )

        assert response.status_code == 410

        assert response.get_json() == {
            "error": "OTP challenge expired.",
            "verified": False,
            "attempts_remaining": 0,
        }

    finally:
        _cleanup(app)


def test_verified_grant_allows_only_same_resource(
    monkeypatch,
) -> None:
    (
        app,
        client,
        user_id,
        session_id,
        email,
        delivered,
    ) = _authenticated_app(
        monkeypatch,
        suffix="scope",
    )

    try:
        _create_pending_challenge(
            app,
            session_id=session_id,
            user_id=user_id,
            email=email,
            resource="finance_page",
        )

        with app.app_context():
            verified = otp_service.verify_otp_code(
                session_id=session_id,
                user_id=user_id,
                otp_code=TEST_OTP,
            )

            assert verified["verified"] is True

        delivered.clear()

        # The policy still evaluates to OTP, but the valid grant
        # satisfies that step-up requirement for finance_page.
        finance = client.get(
            "/api/resources/finance",
            headers={
                "User-Agent": "OtpContractBrowser/1.0",
            },
        )

        assert finance.status_code == 200

        assert finance.get_json() == {
            "title": "Finance Page",
            "sensitivity": "high",
            "message": "Sensitive financial records.",
        }

        # A valid finance grant must not become a session-wide bypass.
        hr = client.get(
            "/api/resources/hr",
            headers={
                "User-Agent": "OtpContractBrowser/1.0",
            },
        )

        assert hr.status_code == 401

        assert hr.get_json() == {
            "error": "OTP verification required.",
            "policy_action": "OTP",
            "requires_otp": True,
        }

        with app.app_context():
            finance_rows = (
                OtpChallenge.query
                .filter_by(
                    session_id=session_id,
                    user_id=user_id,
                    resource="finance_page",
                )
                .all()
            )

            hr_rows = (
                OtpChallenge.query
                .filter_by(
                    session_id=session_id,
                    user_id=user_id,
                    resource="hr_page",
                )
                .all()
            )

            # The verified finance grant must be reused rather than
            # creating another finance OTP challenge.
            assert len(finance_rows) == 1

            # The other resource requires its own challenge.
            assert len(hr_rows) == 1

    finally:
        _cleanup(app)
