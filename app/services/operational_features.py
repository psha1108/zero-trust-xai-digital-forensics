"""Pure helpers for constructing live operational ML features."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta
from typing import Any, Final


WORKING_HOUR_START: Final[int] = 8
WORKING_HOUR_END: Final[int] = 18

RESOURCE_SENSITIVITY_SCORE: Final[dict[str, int]] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

SENSITIVE_RESOURCE_LEVELS: Final[frozenset[str]] = frozenset(
    {"high", "critical"}
)


def is_working_hour(login_hour: int) -> int:
    """Return 1 when the login hour is within the operational work window."""

    if not isinstance(login_hour, int) or isinstance(login_hour, bool):
        raise TypeError("login_hour must be an integer.")

    if not 0 <= login_hour <= 23:
        raise ValueError("login_hour must be from 0 through 23.")

    return int(
        WORKING_HOUR_START
        <= login_hour
        <= WORKING_HOUR_END
    )


def calculate_session_duration_minutes(
    started_at: datetime,
    event_time: datetime,
) -> float:
    """Return non-negative elapsed session duration in minutes."""

    if not isinstance(started_at, datetime):
        raise TypeError("started_at must be a datetime.")

    if not isinstance(event_time, datetime):
        raise TypeError("event_time must be a datetime.")

    elapsed_seconds = (
        event_time - started_at
    ).total_seconds()

    return max(
        0.0,
        elapsed_seconds / 60.0,
    )


def calculate_access_count_5min(
    event_times: Iterable[datetime],
    current_time: datetime,
) -> int:
    """Count events in the inclusive five-minute window ending now."""

    if not isinstance(current_time, datetime):
        raise TypeError("current_time must be a datetime.")

    window_start = current_time - timedelta(minutes=5)

    count = 0

    for event_time in event_times:
        if not isinstance(event_time, datetime):
            raise TypeError(
                "Access event times must be datetime values."
            )

        if window_start <= event_time <= current_time:
            count += 1

    return count


def calculate_failed_attempt_count(
    historical_outcomes: Iterable[bool],
) -> int:
    """
    Count consecutive failed logins immediately before the current success.

    Historical outcomes must be supplied oldest to newest, where True means
    success and False means failure.
    """

    outcomes = list(historical_outcomes)

    count = 0

    for success in reversed(outcomes):
        if not isinstance(success, bool):
            raise TypeError(
                "Login outcomes must contain boolean values."
            )

        if success:
            break

        count += 1

    return count


def calculate_is_new_ip(
    current_ip: str,
    prior_successful_ips: Iterable[str],
) -> int:
    """Return 1 when the current login IP has not been seen successfully."""

    if not isinstance(current_ip, str) or not current_ip:
        raise ValueError(
            "current_ip must be a non-empty string."
        )

    prior_ips = set(prior_successful_ips)

    return int(current_ip not in prior_ips)


def calculate_is_new_device(
    current_device_fingerprint: str,
    prior_successful_device_fingerprints: Iterable[str],
) -> int:
    """Return 1 when the device fingerprint is new for the user."""

    if (
        not isinstance(current_device_fingerprint, str)
        or not current_device_fingerprint
    ):
        raise ValueError(
            "current_device_fingerprint must be a non-empty string."
        )

    prior_devices = set(
        prior_successful_device_fingerprints
    )

    return int(
        current_device_fingerprint
        not in prior_devices
    )


def _event_value(
    event: Mapping[str, Any] | Any,
    field: str,
    default: Any,
) -> Any:
    """Read a field from either a mapping or an ORM-like object."""

    if isinstance(event, Mapping):
        return event.get(field, default)

    return getattr(event, field, default)


def calculate_session_flags(
    events: Iterable[Mapping[str, Any] | Any],
) -> dict[str, int]:
    """Aggregate cumulative security indicators for the current session."""

    unauthorized_access_attempt = 0
    ip_changed_during_session = 0
    device_changed_during_session = 0
    sensitive_resource_access_count = 0

    for event in events:
        if bool(
            _event_value(
                event,
                "privilege_mismatch",
                False,
            )
        ):
            unauthorized_access_attempt = 1

        if bool(
            _event_value(
                event,
                "ip_changed",
                False,
            )
        ):
            ip_changed_during_session = 1

        if bool(
            _event_value(
                event,
                "device_changed",
                False,
            )
        ):
            device_changed_during_session = 1

        sensitivity = str(
            _event_value(
                event,
                "resource_sensitivity",
                "",
            )
        ).lower()

        if sensitivity in SENSITIVE_RESOURCE_LEVELS:
            sensitive_resource_access_count += 1

    return {
        "unauthorized_access_attempt": (
            unauthorized_access_attempt
        ),
        "ip_changed_during_session": (
            ip_changed_during_session
        ),
        "device_changed_during_session": (
            device_changed_during_session
        ),
        "sensitive_resource_access_count": (
            sensitive_resource_access_count
        ),
    }


def build_operational_feature_record(
    *,
    role: str,
    login_event: Any,
    session: Any,
    prior_login_events: Iterable[Any],
    current_access_event: Any,
    session_access_events: Iterable[Any],
) -> dict[str, Any]:
    """
    Build one exact 14-feature operational record for ML inference.

    The returned dictionary order intentionally matches the frozen
    Random Forest source-feature contract.
    """

    from app.utils.fingerprint import get_device_fingerprint

    approved_roles = {
        "admin",
        "employee",
        "finance_user",
        "guest",
        "hr_user",
    }

    if role not in approved_roles:
        raise ValueError(
            f"Unsupported operational role: {role!r}."
        )

    login_time = getattr(
        login_event,
        "timestamp",
        None,
    )

    if not isinstance(login_time, datetime):
        raise ValueError(
            "login_event.timestamp must be a datetime."
        )

    if getattr(login_event, "success", None) is not True:
        raise ValueError(
            "Operational records require a successful login event."
        )

    session_started_at = getattr(
        session,
        "started_at",
        None,
    )

    if not isinstance(session_started_at, datetime):
        raise ValueError(
            "session.started_at must be a datetime."
        )

    current_access_time = getattr(
        current_access_event,
        "timestamp",
        None,
    )

    if not isinstance(current_access_time, datetime):
        raise ValueError(
            "current_access_event.timestamp must be a datetime."
        )

    current_sensitivity = str(
        getattr(
            current_access_event,
            "resource_sensitivity",
            "",
        )
    ).lower()

    if current_sensitivity not in RESOURCE_SENSITIVITY_SCORE:
        raise ValueError(
            "current_access_event.resource_sensitivity "
            "must be low, medium, high, or critical."
        )

    current_ip = getattr(
        session,
        "start_ip",
        None,
    )

    current_device_fingerprint = getattr(
        session,
        "start_device_fingerprint",
        None,
    )

    prior_events = list(prior_login_events)

    for event in prior_events:
        timestamp = getattr(
            event,
            "timestamp",
            None,
        )

        if not isinstance(timestamp, datetime):
            raise ValueError(
                "Prior login events must contain datetime timestamps."
            )

        success = getattr(
            event,
            "success",
            None,
        )

        if not isinstance(success, bool):
            raise ValueError(
                "Prior login events must contain boolean success values."
            )

    prior_events.sort(
        key=lambda event: event.timestamp
    )

    historical_outcomes = [
        event.success
        for event in prior_events
    ]

    prior_successful_events = [
        event
        for event in prior_events
        if event.success
    ]

    prior_successful_ips = [
        event.ip_address
        for event in prior_successful_events
        if isinstance(
            getattr(event, "ip_address", None),
            str,
        )
        and event.ip_address
    ]

    prior_successful_device_fingerprints = [
        get_device_fingerprint(
            event.device_info
        )
        for event in prior_successful_events
        if isinstance(
            getattr(event, "device_info", None),
            str,
        )
        and event.device_info
    ]

    access_events = [
        event
        for event in session_access_events
        if isinstance(
            getattr(event, "timestamp", None),
            datetime,
        )
        and event.timestamp <= current_access_time
    ]

    if current_access_event not in access_events:
        access_events.append(
            current_access_event
        )

    access_event_times = [
        event.timestamp
        for event in access_events
    ]

    session_flags = calculate_session_flags(
        access_events
    )

    login_hour = login_time.hour
    working_hour = is_working_hour(
        login_hour
    )

    record = {
        "role": role,
        "login_hour": login_hour,
        "is_working_hour": working_hour,
        "failed_attempt_count": (
            calculate_failed_attempt_count(
                historical_outcomes
            )
        ),
        "is_new_ip": calculate_is_new_ip(
            current_ip,
            prior_successful_ips,
        ),
        "is_new_device": calculate_is_new_device(
            current_device_fingerprint,
            prior_successful_device_fingerprints,
        ),
        "is_unusual_time": int(
            working_hour == 0
        ),
        "session_duration_minutes": (
            calculate_session_duration_minutes(
                session_started_at,
                current_access_time,
            )
        ),
        "resource_sensitivity_score": (
            RESOURCE_SENSITIVITY_SCORE[
                current_sensitivity
            ]
        ),
        "access_count_5min": (
            calculate_access_count_5min(
                access_event_times,
                current_access_time,
            )
        ),
        "unauthorized_access_attempt": (
            session_flags[
                "unauthorized_access_attempt"
            ]
        ),
        "ip_changed_during_session": (
            session_flags[
                "ip_changed_during_session"
            ]
        ),
        "device_changed_during_session": (
            session_flags[
                "device_changed_during_session"
            ]
        ),
        "sensitive_resource_access_count": (
            session_flags[
                "sensitive_resource_access_count"
            ]
        ),
    }

    return record


def build_operational_feature_record_from_database(
    *,
    session_id: str,
    access_event_id: int,
) -> dict[str, Any]:
    """
    Build the exact operational ML feature record from persisted Flask data.

    Database retrieval is deliberately kept in the backend service layer.
    The standalone ML modules remain independent of Flask and SQLAlchemy.
    """

    from app.models import AccessEvent, LoginEvent, Session, User

    if not isinstance(session_id, str) or not session_id:
        raise ValueError(
            "session_id must be a non-empty string."
        )

    if (
        not isinstance(access_event_id, int)
        or isinstance(access_event_id, bool)
        or access_event_id <= 0
    ):
        raise ValueError(
            "access_event_id must be a positive integer."
        )

    session = Session.query.filter_by(
        session_id=session_id
    ).first()

    if session is None:
        raise ValueError(
            f"Session not found: {session_id!r}."
        )

    user = User.query.filter_by(
        id=session.user_id
    ).first()

    if user is None:
        raise ValueError(
            "Session references a user that does not exist."
        )

    login_event = LoginEvent.query.filter_by(
        id=session.login_event_id
    ).first()

    if login_event is None:
        raise ValueError(
            "Session references a login event that does not exist."
        )

    if login_event.user_id != session.user_id:
        raise ValueError(
            "Session/login-event user mismatch."
        )

    if login_event.success is not True:
        raise ValueError(
            "Session login event must be successful."
        )

    current_access_event = AccessEvent.query.filter_by(
        id=access_event_id
    ).first()

    if current_access_event is None:
        raise ValueError(
            f"Access event not found: {access_event_id}."
        )

    if current_access_event.session_id != session.session_id:
        raise ValueError(
            "Access event does not belong to the requested session."
        )

    if current_access_event.user_id != session.user_id:
        raise ValueError(
            "Access event user does not match the session user."
        )

    prior_login_events = (
        LoginEvent.query
        .filter(
            LoginEvent.user_id == session.user_id,
            LoginEvent.id < login_event.id,
        )
        .order_by(
            LoginEvent.id.asc()
        )
        .all()
    )

    session_access_events = (
        AccessEvent.query
        .filter(
            AccessEvent.user_id == session.user_id,
            AccessEvent.session_id == session.session_id,
            AccessEvent.id <= current_access_event.id,
        )
        .order_by(
            AccessEvent.timestamp.asc(),
            AccessEvent.id.asc(),
        )
        .all()
    )

    return build_operational_feature_record(
        role=user.role,
        login_event=login_event,
        session=session,
        prior_login_events=prior_login_events,
        current_access_event=current_access_event,
        session_access_events=session_access_events,
    )