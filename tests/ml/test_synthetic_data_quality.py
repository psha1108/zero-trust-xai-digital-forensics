import os
import pandas as pd
import pytest

DATA_DIR = "data/synthetic"

def test_files_exist():
    assert os.path.exists(f"{DATA_DIR}/login_events.csv")
    assert os.path.exists(f"{DATA_DIR}/sessions.csv")
    assert os.path.exists(f"{DATA_DIR}/access_events.csv")
    assert os.path.exists(f"{DATA_DIR}/ml_training_dataset.csv")

def test_login_events_columns():
    df = pd.read_csv(f"{DATA_DIR}/login_events.csv")
    required = ["login_event_id", "user_id", "username", "role", "event_time",
                "ip_address", "device_id", "browser", "operating_system",
                "login_status", "failed_attempt_count", "is_new_ip",
                "is_new_device", "is_unusual_time", "scenario_type", "risk_label"]
    for col in required:
        assert col in df.columns

def test_sessions_columns():
    df = pd.read_csv(f"{DATA_DIR}/sessions.csv")
    required = ["session_id", "user_id", "login_event_id", "session_start",
                "session_end", "session_duration_minutes", "ip_address",
                "device_id", "session_status", "risk_label", "scenario_type"]
    for col in required:
        assert col in df.columns

def test_access_events_columns():
    df = pd.read_csv(f"{DATA_DIR}/access_events.csv")
    required = ["access_event_id", "session_id", "user_id", "event_time",
                "resource_name", "resource_type", "resource_sensitivity",
                "access_action", "access_status", "is_authorized_resource",
                "request_count_5min", "ip_changed_during_session",
                "device_changed_during_session", "scenario_type", "risk_label"]
    for col in required:
        assert col in df.columns

def test_ml_dataset_columns():
    df = pd.read_csv(f"{DATA_DIR}/ml_training_dataset.csv")
    required = ["user_id", "role", "login_hour", "is_working_hour",
                "failed_attempt_count", "is_new_ip", "is_new_device",
                "is_unusual_time", "session_duration_minutes",
                "resource_sensitivity_score", "access_count_5min",
                "unauthorized_access_attempt", "ip_changed_during_session",
                "device_changed_during_session", "sensitive_resource_access_count",
                "scenario_type", "risk_label"]
    for col in required:
        assert col in df.columns

def test_risk_labels_valid():
    df = pd.read_csv(f"{DATA_DIR}/ml_training_dataset.csv")
    assert set(df["risk_label"].unique()).issubset({"low", "medium", "high"})

def test_connections():
    logins = pd.read_csv(f"{DATA_DIR}/login_events.csv")
    sessions = pd.read_csv(f"{DATA_DIR}/sessions.csv")
    accesses = pd.read_csv(f"{DATA_DIR}/access_events.csv")

    assert sessions["login_event_id"].isin(logins["login_event_id"]).all()
    assert accesses["session_id"].isin(sessions["session_id"]).all()

def test_binary_columns():
    df = pd.read_csv(f"{DATA_DIR}/ml_training_dataset.csv")
    bin_cols = ["is_working_hour", "is_new_ip", "is_new_device", "is_unusual_time",
                "unauthorized_access_attempt", "ip_changed_during_session",
                "device_changed_during_session"]
    for col in bin_cols:
        assert set(df[col].dropna().unique()).issubset({0, 1, 0.0, 1.0, True, False})

def test_resource_sensitivity_score_is_numeric():
    df = pd.read_csv(f"{DATA_DIR}/ml_training_dataset.csv")
    assert pd.api.types.is_numeric_dtype(df["resource_sensitivity_score"])

def test_scenarios_exist():
    df = pd.read_csv(f"{DATA_DIR}/ml_training_dataset.csv")
    assert "high" in df["risk_label"].values

    counts = df["risk_label"].value_counts(normalize=True)
    assert counts.get("low", 0) > counts.get("medium", 0)
    assert counts.get("medium", 0) > counts.get("high", 0)

def test_all_ip_addresses_are_valid():
    from ipaddress import IPv4Address, ip_address

    files_with_ip = ["login_events.csv", "sessions.csv"]

    for filename in files_with_ip:
        filepath = f"{DATA_DIR}/{filename}"
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            if "ip_address" in df.columns:
                for idx, value in df["ip_address"].dropna().items():
                    try:
                        parsed = ip_address(value)
                        assert isinstance(parsed, IPv4Address), f"Not an IPv4 address in {filename} at index {idx}: {value}"
                    except ValueError:
                        pytest.fail(f"Invalid IP string in {filename} at index {idx}: {value}")
