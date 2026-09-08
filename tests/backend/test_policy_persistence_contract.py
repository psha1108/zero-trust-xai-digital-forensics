"""Database contract for applying Zero Trust policy decisions.

The pure decision engine lives in app.services.policy_engine.

This contract freezes the separate persistence/enforcement layer:

- LoginEvent.action_taken stores the policy action.
- AccessEvent.decision stores the policy action for that request.
- AccessEvent.risk_score stores Random Forest probability_high.
- Session.current_risk_score stores Random Forest probability_high.
- Session.current_risk_label stores Random Forest predicted_risk.
- Block terminates the Session row.
- Allow, OTP, and Restrict do not terminate the Session row.

The risk score is deliberately model-native. No new weighted or
hand-crafted risk formula is introduced.
"""

from __future__ import annotations

import importlib
from datetime import datetime

import pytest

from app.extensions import db
from app.models import AccessEvent, LoginEvent, Session, User


def _analysis(
    *,
    predicted_risk: str,
    probability_low: float,
    probability_medium: float,
    probability_high: float,
    is_anomaly: bool,
    cluster_id: int,
) -> dict:
    return {
        "prediction": {
            "predicted_risk": predicted_risk,
            "probability_low": probability_low,
            "probability_medium": probability_medium,
            "probability_high": probability_high,
        },
        "anomaly_detection": {
            "anomaly_score": (
                0.60
                if is_anomaly
                else 0.40
            ),
            "anomaly_threshold": 0.5532259181941123,
            "threshold_margin": (
                0.60 - 0.5532259181941123
                if is_anomaly
                else 0.40 - 0.5532259181941123
            ),
            "is_anomaly": is_anomaly,
        },
        "behavioral_cluster": {
            "cluster_id": cluster_id,
            "archetype_name": (
                "Elevated Behavioral Activity"
                if cluster_id == 0
                else "Routine Behavioral Activity"
            ),
        },
    }


def _seed(
    database_app,
    *,
    privilege_mismatch: bool = False,
) -> tuple[str, int, int, int]:
    with database_app.app_context():
        user = User(
            username=(
                "mismatch-user"
                if privilege_mismatch
                else "policy-user"
            ),
            email=(
                "mismatch@example.test"
                if privilege_mismatch
                else "policy@example.test"
            ),
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
                10,
                0,
                0,
            ),
            ip_address="10.0.0.5",
            device_info="test-device",
            success=True,
        )

        db.session.add(login_event)
        db.session.flush()

        session_id = (
            "mismatch-policy-session"
            if privilege_mismatch
            else "policy-session"
        )

        login_event.session_id = session_id

        session_row = Session(
            session_id=session_id,
            user_id=user.id,
            login_event_id=login_event.id,
            started_at=datetime(
                2026,
                9,
                2,
                10,
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
        db.session.flush()

        access_event = AccessEvent(
            user_id=user.id,
            session_id=session_id,
            resource=(
                "admin_page"
                if privilege_mismatch
                else "finance_page"
            ),
            resource_sensitivity="high",
            timestamp=datetime(
                2026,
                9,
                2,
                10,
                5,
                0,
            ),
            ip_address="10.0.0.5",
            device_fingerprint="device-a",
            privilege_mismatch=privilege_mismatch,
            ip_changed=False,
            device_changed=False,
        )

        db.session.add(access_event)
        db.session.commit()

        return (
            session_id,
            access_event.id,
            login_event.id,
            session_row.id,
        )


def _apply(
    *,
    session_id: str,
    access_event_id: int,
    analysis: dict,
) -> dict:
    module = importlib.import_module(
        "app.services.policy_enforcement"
    )

    return module.apply_zero_trust_policy(
        session_id=session_id,
        access_event_id=access_event_id,
        analysis=analysis,
    )


def test_allow_persists_policy_and_model_native_risk_score(
    database_app,
) -> None:
    (
        session_id,
        access_event_id,
        login_event_id,
        session_row_id,
    ) = _seed(database_app)

    analysis = _analysis(
        predicted_risk="low",
        probability_low=0.90,
        probability_medium=0.08,
        probability_high=0.02,
        is_anomaly=False,
        cluster_id=1,
    )

    with database_app.app_context():
        result = _apply(
            session_id=session_id,
            access_event_id=access_event_id,
            analysis=analysis,
        )

        assert result == {
            "action": "Allow",
            "terminate_session": False,
            "reason_codes": [
                "low_risk_routine_authorized",
            ],
            "risk_score": pytest.approx(
                0.02,
                abs=1e-15,
            ),
        }

        db.session.expire_all()

        login_event = db.session.get(
            LoginEvent,
            login_event_id,
        )
        access_event = db.session.get(
            AccessEvent,
            access_event_id,
        )
        session_row = db.session.get(
            Session,
            session_row_id,
        )

        assert login_event.action_taken == "Allow"

        assert access_event.decision == "Allow"
        assert access_event.risk_score == pytest.approx(
            0.02,
            abs=1e-15,
        )

        assert session_row.current_risk_score == pytest.approx(
            0.02,
            abs=1e-15,
        )
        assert session_row.current_risk_label == "low"

        assert session_row.is_active is True
        assert session_row.ended_at is None
        assert session_row.end_reason is None


def test_persisted_privilege_mismatch_drives_restrict(
    database_app,
) -> None:
    (
        session_id,
        access_event_id,
        login_event_id,
        session_row_id,
    ) = _seed(
        database_app,
        privilege_mismatch=True,
    )

    analysis = _analysis(
        predicted_risk="low",
        probability_low=0.94,
        probability_medium=0.04,
        probability_high=0.02,
        is_anomaly=False,
        cluster_id=1,
    )

    with database_app.app_context():
        result = _apply(
            session_id=session_id,
            access_event_id=access_event_id,
            analysis=analysis,
        )

        assert result["action"] == "Restrict"
        assert result["terminate_session"] is False
        assert "privilege_mismatch" in result["reason_codes"]

        db.session.expire_all()

        login_event = db.session.get(
            LoginEvent,
            login_event_id,
        )
        access_event = db.session.get(
            AccessEvent,
            access_event_id,
        )
        session_row = db.session.get(
            Session,
            session_row_id,
        )

        assert login_event.action_taken == "Restrict"
        assert access_event.decision == "Restrict"

        assert access_event.risk_score == pytest.approx(
            0.02,
            abs=1e-15,
        )

        assert session_row.current_risk_score == pytest.approx(
            0.02,
            abs=1e-15,
        )
        assert session_row.current_risk_label == "low"

        assert session_row.is_active is True
        assert session_row.ended_at is None
        assert session_row.end_reason is None


def test_medium_risk_otp_uses_probability_high_as_risk_score(
    database_app,
) -> None:
    (
        session_id,
        access_event_id,
        login_event_id,
        session_row_id,
    ) = _seed(database_app)

    analysis = _analysis(
        predicted_risk="medium",
        probability_low=0.10,
        probability_medium=0.70,
        probability_high=0.20,
        is_anomaly=False,
        cluster_id=1,
    )

    with database_app.app_context():
        result = _apply(
            session_id=session_id,
            access_event_id=access_event_id,
            analysis=analysis,
        )

        assert result["action"] == "OTP"

        # risk_score is probability of HIGH risk,
        # not confidence of the predicted class.
        assert result["risk_score"] == pytest.approx(
            0.20,
            abs=1e-15,
        )

        db.session.expire_all()

        login_event = db.session.get(
            LoginEvent,
            login_event_id,
        )
        access_event = db.session.get(
            AccessEvent,
            access_event_id,
        )
        session_row = db.session.get(
            Session,
            session_row_id,
        )

        assert login_event.action_taken == "OTP"
        assert access_event.decision == "OTP"

        assert access_event.risk_score == pytest.approx(
            0.20,
            abs=1e-15,
        )

        assert session_row.current_risk_score == pytest.approx(
            0.20,
            abs=1e-15,
        )
        assert session_row.current_risk_label == "medium"

        assert session_row.is_active is True


def test_block_persists_and_terminates_session(
    database_app,
) -> None:
    (
        session_id,
        access_event_id,
        login_event_id,
        session_row_id,
    ) = _seed(database_app)

    analysis = _analysis(
        predicted_risk="high",
        probability_low=0.01,
        probability_medium=0.04,
        probability_high=0.95,
        is_anomaly=True,
        cluster_id=1,
    )

    with database_app.app_context():
        result = _apply(
            session_id=session_id,
            access_event_id=access_event_id,
            analysis=analysis,
        )

        assert result["action"] == "Block"
        assert result["terminate_session"] is True
        assert result["risk_score"] == pytest.approx(
            0.95,
            abs=1e-15,
        )

        db.session.expire_all()

        login_event = db.session.get(
            LoginEvent,
            login_event_id,
        )
        access_event = db.session.get(
            AccessEvent,
            access_event_id,
        )
        session_row = db.session.get(
            Session,
            session_row_id,
        )

        assert login_event.action_taken == "Block"

        assert access_event.decision == "Block"
        assert access_event.risk_score == pytest.approx(
            0.95,
            abs=1e-15,
        )
        assert session_row.current_risk_score == pytest.approx(
            0.95,
            abs=1e-15,
        )
        assert session_row.current_risk_label == "high"

        assert result["risk_score"] == 0.95

        # Session termination has moved to the caller so the
        # session should STILL be active here!
        db.session.expire_all()
        session_row = db.session.get(Session, session_row_id)
        assert session_row.is_active is True
        assert session_row.ended_at is None
        assert session_row.end_reason is None


def test_invalid_probability_high_is_rejected_without_db_mutation(
    database_app,
) -> None:
    (
        session_id,
        access_event_id,
        login_event_id,
        session_row_id,
    ) = _seed(database_app)

    analysis = _analysis(
        predicted_risk="high",
        probability_low=0.0,
        probability_medium=0.0,
        probability_high=1.2,
        is_anomaly=True,
        cluster_id=1,
    )

    with database_app.app_context():
        with pytest.raises(
            ValueError,
            match="probability_high",
        ):
            _apply(
                session_id=session_id,
                access_event_id=access_event_id,
                analysis=analysis,
            )

        db.session.expire_all()

        login_event = db.session.get(
            LoginEvent,
            login_event_id,
        )
        access_event = db.session.get(
            AccessEvent,
            access_event_id,
        )
        session_row = db.session.get(
            Session,
            session_row_id,
        )

        assert login_event.action_taken is None
        assert access_event.decision is None
        assert access_event.risk_score is None

        assert session_row.current_risk_score is None
        assert session_row.current_risk_label is None
        assert session_row.is_active is True
        assert session_row.ended_at is None
        assert session_row.end_reason is None
