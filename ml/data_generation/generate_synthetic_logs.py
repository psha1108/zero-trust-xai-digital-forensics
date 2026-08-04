import os
import random
import uuid
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

from ml.data_generation.constants import (
    ROLES, BROWSERS, OPERATING_SYSTEMS, RESOURCES,
    RESOURCE_SENSITIVITY, RESOURCE_SENSITIVITY_SCORE,
    WORKING_HOUR_START, WORKING_HOUR_END
)
from ml.data_generation.scenarios import (
    get_scenario_by_risk, generate_ip, generate_device_id, determine_risk_label
)

fake = Faker()

def generate_users(num_users=50):
    users = []
    for _ in range(num_users):
        users.append({
            "user_id": str(uuid.uuid4()),
            "username": fake.user_name(),
            "role": random.choice(ROLES)
        })
    return users

def run_generation():
    print("Generating synthetic data...")
    os.makedirs("data/synthetic", exist_ok=True)

    users = generate_users(50)

    login_events = []
    sessions = []
    access_events = []
    ml_dataset = []

    start_date = datetime.now() - timedelta(days=30)

    num_logins = 1500

    for _ in range(num_logins):
        user = random.choice(users)
        risk_label = determine_risk_label()
        scenario_type = get_scenario_by_risk(risk_label)

        event_time = start_date + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        login_hour = event_time.hour
        is_working_hour = 1 if WORKING_HOUR_START <= login_hour <= WORKING_HOUR_END else 0

        if risk_label == "high":
            failed_attempt_count = random.randint(3, 10)
            is_unusual_time = 1 if is_working_hour == 0 else 0
            login_status = random.choice(["success", "failed", "blocked"])
        elif risk_label == "medium":
            failed_attempt_count = random.randint(1, 3)
            is_unusual_time = random.choice([0, 1])
            login_status = random.choice(["success", "failed"])
        else:
            failed_attempt_count = random.randint(0, 1)
            is_unusual_time = 0
            login_status = "success"

        if "brute_force_then_success" in scenario_type:
            login_status = "success"
            failed_attempt_count = random.randint(5, 15)

        if "multiple_failed_logins" in scenario_type:
            login_status = "blocked"
            failed_attempt_count = random.randint(8, 20)

        login_event_id = str(uuid.uuid4())
        ip_address = generate_ip(is_internal=True) if risk_label == "low" else generate_ip(is_internal=False)
        device_id = generate_device_id()

        is_new_ip = 1 if random.random() < (0.1 if risk_label == "low" else 0.5) else 0
        is_new_device = 1 if random.random() < (0.05 if risk_label == "low" else 0.4) else 0

        if "new_ip_login" in scenario_type:
            is_new_ip = 1
        if "new_device_login" in scenario_type:
            is_new_device = 1

        login_event = {
            "login_event_id": login_event_id,
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "event_time": event_time.isoformat(),
            "ip_address": ip_address,
            "device_id": device_id,
            "browser": random.choice(BROWSERS),
            "operating_system": random.choice(OPERATING_SYSTEMS),
            "login_status": login_status,
            "failed_attempt_count": failed_attempt_count,
            "is_new_ip": is_new_ip,
            "is_new_device": is_new_device,
            "is_unusual_time": is_unusual_time,
            "scenario_type": scenario_type,
            "risk_label": risk_label
        }
        login_events.append(login_event)

        if login_status == "success" and random.random() < 0.8:
            session_id = str(uuid.uuid4())
            session_duration = random.randint(5, 120) if risk_label != "high" else random.randint(1, 400)
            session_end = event_time + timedelta(minutes=session_duration)

            session_status = "ended" if random.random() < 0.9 else "active"
            if "session_hijack_simulation" in scenario_type:
                session_status = "terminated"

            session = {
                "session_id": session_id,
                "user_id": user["user_id"],
                "login_event_id": login_event_id,
                "session_start": event_time.isoformat(),
                "session_end": session_end.isoformat(),
                "session_duration_minutes": session_duration,
                "ip_address": ip_address,
                "device_id": device_id,
                "session_status": session_status,
                "risk_label": risk_label,
                "scenario_type": scenario_type
            }
            sessions.append(session)

            num_accesses = random.randint(1, 10)
            if risk_label == "high":
                num_accesses = random.randint(10, 30)

            ip_changed_during_session = 1 if "ip_change_during_session" in scenario_type else 0
            device_changed_during_session = 1 if "device_change_during_session" in scenario_type else 0

            sensitive_access_count = 0
            unauthorized_access = 0

            for _ in range(num_accesses):
                access_event_id = str(uuid.uuid4())
                access_time = event_time + timedelta(minutes=random.randint(1, max(2, session_duration-1)))

                resource_name = random.choice(RESOURCES)
                sensitivity = RESOURCE_SENSITIVITY[resource_name]

                if risk_label == "low":
                    if sensitivity == "critical" and user["role"] != "admin":
                        resource_name = "dashboard"
                        sensitivity = "low"

                if "sensitive_resource_abuse" in scenario_type:
                    resource_name = random.choice(["admin_panel", "confidential_documents"])
                    sensitivity = "critical"

                is_authorized = 1
                access_status = "allowed"

                if sensitivity in ["high", "critical"] and user["role"] in ["guest", "employee"]:
                    is_authorized = 0
                    access_status = "blocked" if random.random() < 0.8 else "restricted"
                    unauthorized_access = 1

                if user["role"] == "admin" and "unauthorized_admin_access" in scenario_type:
                    is_authorized = 0
                    access_status = "restricted"
                    unauthorized_access = 1

                if sensitivity in ["high", "critical"]:
                    sensitive_access_count += 1

                access_event = {
                    "access_event_id": access_event_id,
                    "session_id": session_id,
                    "user_id": user["user_id"],
                    "event_time": access_time.isoformat(),
                    "resource_name": resource_name,
                    "resource_type": "web",
                    "resource_sensitivity": sensitivity,
                    "access_action": random.choice(["read", "write", "download"]),
                    "access_status": access_status,
                    "is_authorized_resource": is_authorized,
                    "request_count_5min": random.randint(1, 50) if risk_label == "high" else random.randint(1, 10),
                    "ip_changed_during_session": ip_changed_during_session,
                    "device_changed_during_session": device_changed_during_session,
                    "scenario_type": scenario_type,
                    "risk_label": risk_label
                }
                access_events.append(access_event)

            ml_row = {
                "user_id": user["user_id"],
                "role": user["role"],
                "login_hour": login_hour,
                "is_working_hour": is_working_hour,
                "failed_attempt_count": failed_attempt_count,
                "is_new_ip": is_new_ip,
                "is_new_device": is_new_device,
                "is_unusual_time": is_unusual_time,
                "session_duration_minutes": session_duration,
                "resource_sensitivity_score": RESOURCE_SENSITIVITY_SCORE[sensitivity],
                "access_count_5min": access_event["request_count_5min"],
                "unauthorized_access_attempt": unauthorized_access,
                "ip_changed_during_session": ip_changed_during_session,
                "device_changed_during_session": device_changed_during_session,
                "sensitive_resource_access_count": sensitive_access_count,
                "scenario_type": scenario_type,
                "risk_label": risk_label
            }
            ml_dataset.append(ml_row)

    pd.DataFrame(login_events).to_csv("data/synthetic/login_events.csv", index=False)
    pd.DataFrame(sessions).to_csv("data/synthetic/sessions.csv", index=False)
    pd.DataFrame(access_events).to_csv("data/synthetic/access_events.csv", index=False)
    pd.DataFrame(ml_dataset).to_csv("data/synthetic/ml_training_dataset.csv", index=False)

    print("\nSynthetic data generation completed.\n")
    print(f"login_events.csv: {len(login_events)} rows")
    print(f"sessions.csv: {len(sessions)} rows")
    print(f"access_events.csv: {len(access_events)} rows")
    print(f"ml_training_dataset.csv: {len(ml_dataset)} rows\n")

    df_ml = pd.DataFrame(ml_dataset)
    risk_counts = df_ml["risk_label"].value_counts(normalize=True) * 100

    print("Risk distribution:")
    for label in ["low", "medium", "high"]:
        if label in risk_counts:
            print(f"{label}: {int(risk_counts[label])}%")
        else:
            print(f"{label}: 0%")

if __name__ == "__main__":
    run_generation()
