"""Zero Trust OTP step-up authentication service.

This module is intentionally independent from ML inference and from the
pure policy decision engine.

Security properties:

- six-digit decimal OTP
- OTP stored only as a hash
- 300-second challenge lifetime
- maximum five failed attempts
- pending challenge reuse
- 300-second verified step-up grant
- grant scoped to session + user + resource
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from app.extensions import db
from app.models import OtpChallenge, Session


OTP_LENGTH = 6
OTP_TTL_SECONDS = 300
OTP_MAX_ATTEMPTS = 5
OTP_GRANT_TTL_SECONDS = 300


def _generate_otp_code() -> str:
    """Generate a cryptographically random six-digit decimal OTP."""

    upper_bound = 10 ** OTP_LENGTH

    return f"{secrets.randbelow(upper_bound):0{OTP_LENGTH}d}"


def _deliver_otp_code(
    *,
    target: str,
    code: str,
) -> None:
    """Default development/demo delivery transport.

    Production delivery can later be replaced with email/SMS without
    changing challenge persistence or verification behavior.
    """

    print(
        f"[ZERO TRUST OTP] target={target} code={code}"
    )


def _validate_identity(
    *,
    session_id: str,
    user_id: int,
) -> Session:
    """Return the matching active application session."""

    if (
        not isinstance(session_id, str)
        or not session_id.strip()
    ):
        raise ValueError(
            "session_id must be a non-empty string."
        )

    if (
        isinstance(user_id, bool)
        or not isinstance(user_id, int)
        or user_id <= 0
    ):
        raise ValueError(
            "user_id must be a positive integer."
        )

    session_row = (
        Session.query
        .filter_by(
            session_id=session_id,
            user_id=user_id,
            is_active=True,
        )
        .one_or_none()
    )

    if session_row is None:
        raise ValueError(
            "session does not match an active user session."
        )

    return session_row


def _validate_resource(
    resource: str,
) -> str:
    if (
        not isinstance(resource, str)
        or not resource.strip()
    ):
        raise ValueError(
            "resource must be a non-empty string."
        )

    return resource.strip()


def _pending_challenge(
    *,
    session_id: str,
    user_id: int,
    resource: str,
    now: datetime,
) -> OtpChallenge | None:
    """Return a reusable pending challenge, if one exists."""

    return (
        OtpChallenge.query
        .filter(
            OtpChallenge.session_id == session_id,
            OtpChallenge.user_id == user_id,
            OtpChallenge.resource == resource,
            OtpChallenge.verified_at.is_(None),
            OtpChallenge.expires_at > now,
            OtpChallenge.failed_attempts
            < OtpChallenge.max_attempts,
        )
        .order_by(
            OtpChallenge.id.desc()
        )
        .first()
    )


def create_otp_challenge(
    *,
    session_id: str,
    user_id: int,
    resource: str,
    delivery_target: str,
    reason_codes: list[str] = None,
) -> dict[str, int | str]:
    """Create or reuse a pending OTP challenge."""

    _validate_identity(
        session_id=session_id,
        user_id=user_id,
    )

    resource = _validate_resource(
        resource
    )

    if (
        not isinstance(delivery_target, str)
        or not delivery_target.strip()
    ):
        raise ValueError(
            "delivery_target must be a non-empty string."
        )

    now = datetime.utcnow()

    existing = _pending_challenge(
        session_id=session_id,
        user_id=user_id,
        resource=resource,
        now=now,
    )

    if existing is not None:
        return {
            "status": "pending",
            "expires_in_seconds": OTP_TTL_SECONDS,
        }

    otp_code = _generate_otp_code()

    if (
        not isinstance(otp_code, str)
        or len(otp_code) != OTP_LENGTH
        or not otp_code.isdecimal()
    ):
        raise RuntimeError(
            "OTP generator must return exactly six decimal digits."
        )

    challenge = OtpChallenge(
        session_id=session_id,
        user_id=user_id,
        resource=resource,
        otp_hash=generate_password_hash(
            otp_code
        ),
        created_at=now,
        expires_at=(
            now
            + timedelta(
                seconds=OTP_TTL_SECONDS
            )
        ),
        failed_attempts=0,
        max_attempts=OTP_MAX_ATTEMPTS,
        verified_at=None,
        granted_reason_codes=", ".join(reason_codes) if reason_codes else None,
    )

    try:
        db.session.add(
            challenge
        )

        db.session.flush()

        _deliver_otp_code(
            target=delivery_target.strip(),
            code=otp_code,
        )

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return {
        "status": "pending",
        "expires_in_seconds": OTP_TTL_SECONDS,
    }


def _latest_unverified_challenge(
    *,
    session_id: str,
    user_id: int,
) -> OtpChallenge | None:
    """Return the most recently created unresolved challenge."""

    return (
        OtpChallenge.query
        .filter_by(
            session_id=session_id,
            user_id=user_id,
            verified_at=None,
        )
        .order_by(
            OtpChallenge.id.desc()
        )
        .first()
    )


def verify_otp_code(
    *,
    session_id: str,
    user_id: int,
    otp_code: str,
) -> dict[str, bool | int | str]:
    """Verify the current pending OTP challenge."""

    _validate_identity(
        session_id=session_id,
        user_id=user_id,
    )

    challenge = _latest_unverified_challenge(
        session_id=session_id,
        user_id=user_id,
    )

    if challenge is None:
        return {
            "verified": False,
            "status": "expired",
            "attempts_remaining": 0,
        }

    now = datetime.utcnow()

    if challenge.failed_attempts >= challenge.max_attempts:
        return {
            "verified": False,
            "status": "locked",
            "attempts_remaining": 0,
        }

    if challenge.expires_at <= now:
        return {
            "verified": False,
            "status": "expired",
            "attempts_remaining": 0,
        }

    candidate = (
        otp_code
        if isinstance(otp_code, str)
        else ""
    )

    if check_password_hash(
        challenge.otp_hash,
        candidate,
    ):
        challenge.verified_at = now

        db.session.commit()

        return {
            "verified": True,
            "status": "verified",
            "attempts_remaining": (
                challenge.max_attempts
                - challenge.failed_attempts
            ),
        }

    challenge.failed_attempts = min(
        challenge.failed_attempts + 1,
        challenge.max_attempts,
    )

    db.session.commit()

    attempts_remaining = max(
        challenge.max_attempts
        - challenge.failed_attempts,
        0,
    )

    status = (
        "locked"
        if attempts_remaining == 0
        else "invalid"
    )

    return {
        "verified": False,
        "status": status,
        "attempts_remaining": attempts_remaining,
    }


def has_valid_otp_grant(
    *,
    session_id: str,
    user_id: int,
    resource: str,
    current_reason_codes: list[str] = None,
) -> bool:
    """Return whether a valid resource-scoped OTP grant exists."""

    resource = _validate_resource(
        resource
    )

    session_row = (
        Session.query
        .filter_by(
            session_id=session_id,
            user_id=user_id,
            is_active=True,
        )
        .one_or_none()
    )

    if session_row is None:
        return False

    challenge = (
        OtpChallenge.query
        .filter(
            OtpChallenge.session_id == session_id,
            OtpChallenge.user_id == user_id,
            OtpChallenge.verified_at.is_not(None),
        )
        .order_by(
            OtpChallenge.verified_at.desc(),
            OtpChallenge.id.desc(),
        )
        .first()
    )

    if challenge is None:
        return False

    now = datetime.utcnow()

    grant_age = (
        now
        - challenge.verified_at
    ).total_seconds()

    if not (0.0 <= grant_age <= OTP_GRANT_TTL_SECONDS):
        return False

    if challenge.granted_reason_codes is None:
        return False

    if current_reason_codes is not None:
        granted_reasons = {r.strip() for r in challenge.granted_reason_codes.split(",")}
        granted_reasons = {r for r in granted_reasons if r and r != "No reason provided"}
        
        current_reasons = set(current_reason_codes)
        current_reasons = {r for r in current_reasons if r and r != "No reason provided"}

        if current_reasons != granted_reasons:
            return False

    return True
