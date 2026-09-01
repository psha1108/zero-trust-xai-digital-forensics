"""Contract tests for live operational behavioral feature construction."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.services.operational_features import (
    RESOURCE_SENSITIVITY_SCORE,
    WORKING_HOUR_END,
    WORKING_HOUR_START,
    build_operational_feature_record,
    calculate_access_count_5min,
    calculate_failed_attempt_count,
    calculate_is_new_device,
    calculate_is_new_ip,
    calculate_session_duration_minutes,
    calculate_session_flags,
    is_working_hour,
)


def test_working_hour_contract() -> None:
    assert WORKING_HOUR_START == 8
    assert WORKING_HOUR_END == 18

    assert is_working_hour(7) == 0
    assert is_working_hour(8) == 1
    assert is_working_hour(18) == 1
    assert is_working_hour(19) == 0


def test_resource_sensitivity_contract() -> None:
    assert RESOURCE_SENSITIVITY_SCORE == {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }


def test_session_duration_minutes_allows_fractional_values() -> None:
    started_at = datetime(2026, 8, 31, 10, 0, 0)
    event_time = started_at + timedelta(seconds=90)

    assert calculate_session_duration_minutes(
        started_at,
        event_time,
    ) == pytest.approx(1.5)


def test_session_duration_is_never_negative() -> None:
    started_at = datetime(2026, 8, 31, 10, 0, 0)
    event_time = started_at - timedelta(seconds=30)

    assert calculate_session_duration_minutes(
        started_at,
        event_time,
    ) == 0.0


def test_access_count_5min_includes_current_event() -> None:
    current_time = datetime(2026, 8, 31, 10, 10, 0)

    event_times = [
        current_time - timedelta(minutes=6),
        current_time - timedelta(minutes=5),
        current_time - timedelta(minutes=2),
        current_time,
    ]

    assert calculate_access_count_5min(
        event_times,
        current_time,
    ) == 3


def test_failed_attempt_count_is_consecutive_before_success() -> None:
    # Oldest -> newest historical login outcomes before current success.
    outcomes = [
        True,
        False,
        False,
        False,
    ]

    assert calculate_failed_attempt_count(outcomes) == 3


def test_failed_attempt_count_stops_at_previous_success() -> None:
    outcomes = [
        False,
        False,
        True,
        False,
        False,
    ]

    assert calculate_failed_attempt_count(outcomes) == 2


def test_new_ip_uses_prior_successful_login_history() -> None:
    assert calculate_is_new_ip(
        "10.0.0.5",
        ["10.0.0.2", "10.0.0.3"],
    ) == 1

    assert calculate_is_new_ip(
        "10.0.0.3",
        ["10.0.0.2", "10.0.0.3"],
    ) == 0


def test_first_successful_login_counts_as_new_ip() -> None:
    assert calculate_is_new_ip(
        "10.0.0.5",
        [],
    ) == 1


def test_new_device_uses_stable_device_fingerprint_history() -> None:
    assert calculate_is_new_device(
        "chrome-windows",
        ["edge-windows", "firefox-linux"],
    ) == 1

    assert calculate_is_new_device(
        "chrome-windows",
        ["edge-windows", "chrome-windows"],
    ) == 0


def test_first_successful_login_counts_as_new_device() -> None:
    assert calculate_is_new_device(
        "chrome-windows",
        [],
    ) == 1


def test_session_flags_are_cumulative() -> None:
    events = [
        {
            "privilege_mismatch": False,
            "ip_changed": False,
            "device_changed": False,
            "resource_sensitivity": "low",
        },
        {
            "privilege_mismatch": True,
            "ip_changed": False,
            "device_changed": False,
            "resource_sensitivity": "high",
        },
        {
            "privilege_mismatch": False,
            "ip_changed": True,
            "device_changed": True,
            "resource_sensitivity": "medium",
        },
    ]

    flags = calculate_session_flags(events)

    assert flags == {
        "unauthorized_access_attempt": 1,
        "ip_changed_during_session": 1,
        "device_changed_during_session": 1,
        "sensitive_resource_access_count": 1,
    }


def test_sensitive_access_count_includes_high_and_critical() -> None:
    events = [
        {
            "privilege_mismatch": False,
            "ip_changed": False,
            "device_changed": False,
            "resource_sensitivity": "high",
        },
        {
            "privilege_mismatch": False,
            "ip_changed": False,
            "device_changed": False,
            "resource_sensitivity": "critical",
        },
    ]

    flags = calculate_session_flags(events)

    assert flags["sensitive_resource_access_count"] == 2


from types import SimpleNamespace

from ml.classification.preprocessing import (
    MODEL_FEATURE_COLUMNS,
    select_random_forest_features,
)


def test_build_operational_feature_record_matches_rf_contract() -> None:
    login_time = datetime(2026, 8, 31, 10, 0, 0)

    login_event = SimpleNamespace(
        timestamp=login_time,
        ip_address="10.0.0.5",
        device_info=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
        ),
        success=True,
    )

    session = SimpleNamespace(
        started_at=login_time,
        start_ip="10.0.0.5",
        start_device_fingerprint="chrome-windows",
    )

    prior_login_events = [
        SimpleNamespace(
            timestamp=login_time - timedelta(minutes=20),
            ip_address="10.0.0.2",
            device_info="Mozilla/5.0 Windows Firefox/139.0",
            success=True,
        ),
        SimpleNamespace(
            timestamp=login_time - timedelta(minutes=3),
            ip_address="10.0.0.5",
            device_info="Mozilla/5.0 Windows Chrome/140.0",
            success=False,
        ),
        SimpleNamespace(
            timestamp=login_time - timedelta(minutes=2),
            ip_address="10.0.0.5",
            device_info="Mozilla/5.0 Windows Chrome/140.0",
            success=False,
        ),
    ]

    current_access = SimpleNamespace(
        timestamp=login_time + timedelta(minutes=10),
        resource_sensitivity="high",
        privilege_mismatch=True,
        ip_changed=True,
        device_changed=False,
    )

    session_access_events = [
        SimpleNamespace(
            timestamp=login_time + timedelta(minutes=4),
            resource_sensitivity="low",
            privilege_mismatch=False,
            ip_changed=False,
            device_changed=False,
        ),
        SimpleNamespace(
            timestamp=login_time + timedelta(minutes=5),
            resource_sensitivity="critical",
            privilege_mismatch=False,
            ip_changed=False,
            device_changed=True,
        ),
        SimpleNamespace(
            timestamp=login_time + timedelta(minutes=8),
            resource_sensitivity="medium",
            privilege_mismatch=False,
            ip_changed=False,
            device_changed=False,
        ),
        current_access,
    ]

    record = build_operational_feature_record(
        role="employee",
        login_event=login_event,
        session=session,
        prior_login_events=prior_login_events,
        current_access_event=current_access,
        session_access_events=session_access_events,
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


def test_built_record_is_accepted_by_rf_validation() -> None:
    login_time = datetime(2026, 8, 31, 22, 0, 0)

    login_event = SimpleNamespace(
        timestamp=login_time,
        ip_address="192.168.1.10",
        device_info="Mozilla/5.0 Windows Chrome/140.0",
        success=True,
    )

    session = SimpleNamespace(
        started_at=login_time,
        start_ip="192.168.1.10",
        start_device_fingerprint="chrome-windows",
    )

    current_access = SimpleNamespace(
        timestamp=login_time + timedelta(seconds=90),
        resource_sensitivity="low",
        privilege_mismatch=False,
        ip_changed=False,
        device_changed=False,
    )

    record = build_operational_feature_record(
        role="admin",
        login_event=login_event,
        session=session,
        prior_login_events=[],
        current_access_event=current_access,
        session_access_events=[current_access],
    )

    assert record["is_working_hour"] == 0
    assert record["is_unusual_time"] == 1
    assert record["is_new_ip"] == 1
    assert record["is_new_device"] == 1
    assert record["session_duration_minutes"] == pytest.approx(1.5)

    import pandas as pd

    selected = select_random_forest_features(
        pd.DataFrame([record])
    )

    assert selected.shape == (1, 14)
    assert selected.columns.tolist() == MODEL_FEATURE_COLUMNS
