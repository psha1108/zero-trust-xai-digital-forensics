"""Persistence and session-enforcement layer for Zero Trust policy.

The pure decision rules remain in app.services.policy_engine.

This module applies one already-computed operational ML analysis to the
persisted access/session state. It does not execute or retrain ML models.

Persistence contract:

- LoginEvent.action_taken <- policy action
- AccessEvent.decision <- policy action
- AccessEvent.risk_score <- Random Forest probability_high
- Session.current_risk_score <- Random Forest probability_high
- Session.current_risk_label <- Random Forest predicted_risk

Only a Block decision terminates the complete session.
Allow, OTP, and Restrict keep the session active.
"""

from __future__ import annotations

from datetime import datetime
from math import isfinite
from numbers import Real
from typing import Any, Mapping

from app.extensions import db
from app.models import AccessEvent, LoginEvent, Session
from app.services.policy_engine import decide_zero_trust_policy
from app.services.otp_service import count_recent_evasions


def _extract_risk_state(
    analysis: Mapping[str, Any],
) -> tuple[str, float]:
    """Extract and validate the persisted RF risk state."""

    if not isinstance(analysis, Mapping):
        raise TypeError(
            "analysis must be a mapping."
        )

    prediction = analysis.get(
        "prediction"
    )

    if not isinstance(
        prediction,
        Mapping,
    ):
        raise TypeError(
            "analysis['prediction'] must be a mapping."
        )

    predicted_risk = prediction.get(
        "predicted_risk"
    )

    if predicted_risk not in {
        "low",
        "medium",
        "high",
    }:
        raise ValueError(
            "predicted_risk must be low, medium, or high."
        )

    probability_high = prediction.get(
        "probability_high"
    )

    if (
        isinstance(probability_high, bool)
        or not isinstance(
            probability_high,
            Real,
        )
    ):
        raise TypeError(
            "probability_high must be a real number."
        )

    risk_score = float(
        probability_high
    )

    if (
        not isfinite(risk_score)
        or risk_score < 0.0
        or risk_score > 1.0
    ):
        raise ValueError(
            "probability_high must be finite and between 0 and 1."
        )

    return (
        predicted_risk,
        risk_score,
    )


def apply_zero_trust_policy(
    *,
    session_id: str,
    access_event_id: int,
    analysis: Mapping[str, Any],
) -> dict[str, Any]:
    """Decide, persist, and apply policy for one access event.

    The persisted AccessEvent is the source of truth for
    privilege_mismatch. The caller cannot override authorization
    evidence through the analysis payload.

    This function assumes the ML analysis for the same access event has
    already completed successfully.
    """

    if (
        not isinstance(session_id, str)
        or not session_id.strip()
    ):
        raise ValueError(
            "session_id must be a non-empty string."
        )

    if (
        isinstance(access_event_id, bool)
        or not isinstance(
            access_event_id,
            int,
        )
        or access_event_id <= 0
    ):
        raise ValueError(
            "access_event_id must be a positive integer."
        )

    (
        predicted_risk,
        risk_score,
    ) = _extract_risk_state(
        analysis
    )

    access_event = db.session.get(
        AccessEvent,
        access_event_id,
    )

    if access_event is None:
        raise LookupError(
            "AccessEvent was not found."
        )

    if access_event.session_id != session_id:
        raise ValueError(
            "AccessEvent does not belong to the supplied session."
        )

    session_row = (
        Session.query
        .filter_by(
            session_id=session_id,
        )
        .one_or_none()
    )

    if session_row is None:
        raise LookupError(
            "Session was not found."
        )

    login_event = db.session.get(
        LoginEvent,
        session_row.login_event_id,
    )

    if login_event is None:
        raise LookupError(
            "Session anchor LoginEvent was not found."
        )

    evasion_count = count_recent_evasions(
        session_id=session_id,
        user_id=access_event.user_id,
        minutes=5,
    )

    policy_result = decide_zero_trust_policy(
        analysis=analysis,
        privilege_mismatch=bool(
            access_event.privilege_mismatch
        ),
        recent_evasion_count=evasion_count,
        is_protected_resource=(access_event.resource in {"normal_page", "hr_page", "finance_page", "it_support", "management_reports"}),
    )

    action = policy_result["action"]
    terminate_session = policy_result["terminate_session"]

    login_event.action_taken = action

    access_event.decision = action
    access_event.risk_score = risk_score

    session_row.current_risk_score = risk_score
    session_row.current_risk_label = predicted_risk

    # Session termination logic has been moved to the caller to ensure
    # the EvidenceLog is created BEFORE the session is terminated.
    db.session.flush()

    return {
        **policy_result,
        "risk_score": risk_score,
    }
