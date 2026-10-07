import pytest
from datetime import datetime, timedelta
from app.services.policy_enforcement import apply_zero_trust_policy
from app.models import AccessEvent, Session, LoginEvent, User
from app.extensions import db

def test_rapid_switch_blocks_after_10(database_app):
    with database_app.app_context():
        user = User(username="test_rapid", email="rapid@test.com", role="employee")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        login = LoginEvent(user_id=user.id, username_attempted=user.username, ip_address="127.0.0.1", timestamp=datetime.utcnow())
        db.session.add(login)
        db.session.commit()

        session = Session(user_id=user.id, login_event_id=login.id, session_id="test_sess_rapid", start_ip="127.0.0.1", current_ip="127.0.0.1", start_device_fingerprint="fp", current_device_fingerprint="fp")
        db.session.add(session)
        db.session.commit()

        base_time = datetime.utcnow()
        resources = ["normal_page", "hr_page", "finance_page", "it_support", "normal_page", "hr_page", "finance_page", "it_support", "normal_page", "finance_page", "hr_page"]
        
        events = []
        for i in range(11):
            event = AccessEvent(
                user_id=user.id,
                session_id="test_sess_rapid",
                resource=resources[i],
                resource_sensitivity="low",
                timestamp=base_time + timedelta(seconds=i * 1.5),
                ip_address="127.0.0.1",
                privilege_mismatch=False
            )
            db.session.add(event)
            db.session.flush()
            events.append(event)
        
        db.session.commit()

        analysis = {
            "prediction": {"predicted_risk": "low", "probability_high": 0.05},
            "anomaly_detection": {"is_anomaly": False, "anomaly_score": -0.1},
            "behavioral_cluster": {"cluster_id": 1, "archetype_name": "normal"},
            "explanation": {}
        }

        # 10 switches achieved on the 11th event (index 10)
        result = apply_zero_trust_policy(
            session_id="test_sess_rapid",
            access_event_id=events[10].id,
            analysis=analysis
        )

        assert result["action"] == "Block"
        assert "rapid_resource_switching" in result["reason_codes"]
        assert result["terminate_session"] is True


def test_rapid_switch_no_block_on_9(database_app):
    with database_app.app_context():
        user = User(username="test_rapid_9", email="rapid9@test.com", role="employee")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        login = LoginEvent(user_id=user.id, username_attempted=user.username, ip_address="127.0.0.1", timestamp=datetime.utcnow())
        db.session.add(login)
        db.session.commit()

        session = Session(user_id=user.id, login_event_id=login.id, session_id="test_sess_rapid_9", start_ip="127.0.0.1", current_ip="127.0.0.1", start_device_fingerprint="fp", current_device_fingerprint="fp")
        db.session.add(session)
        db.session.commit()

        base_time = datetime.utcnow()
        resources = ["normal_page", "hr_page", "finance_page", "it_support", "normal_page", "hr_page", "finance_page", "it_support", "normal_page", "finance_page"]
        
        events = []
        for i in range(10):
            event = AccessEvent(
                user_id=user.id,
                session_id="test_sess_rapid_9",
                resource=resources[i],
                resource_sensitivity="low",
                timestamp=base_time + timedelta(seconds=i * 1.5),
                ip_address="127.0.0.1",
                privilege_mismatch=False
            )
            db.session.add(event)
            db.session.flush()
            events.append(event)
        
        db.session.commit()

        analysis = {
            "prediction": {"predicted_risk": "low", "probability_high": 0.05},
            "anomaly_detection": {"is_anomaly": False, "anomaly_score": -0.1},
            "behavioral_cluster": {"cluster_id": 1, "archetype_name": "normal"},
            "explanation": {}
        }

        # 9 switches achieved on the 10th event (index 9)
        result = apply_zero_trust_policy(
            session_id="test_sess_rapid_9",
            access_event_id=events[9].id,
            analysis=analysis
        )

        assert result["action"] != "Block"


def test_rapid_switch_streak_resets_after_2_seconds(database_app):
    with database_app.app_context():
        user = User(username="test_rapid_reset", email="rapid_r@test.com", role="employee")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        login = LoginEvent(user_id=user.id, username_attempted=user.username, ip_address="127.0.0.1", timestamp=datetime.utcnow())
        db.session.add(login)
        db.session.commit()

        session = Session(user_id=user.id, login_event_id=login.id, session_id="test_sess_rapid_reset", start_ip="127.0.0.1", current_ip="127.0.0.1", start_device_fingerprint="fp", current_device_fingerprint="fp")
        db.session.add(session)
        db.session.commit()

        base_time = datetime.utcnow()
        resources = ["normal_page", "hr_page", "finance_page", "it_support", "normal_page", "hr_page", "finance_page", "it_support", "normal_page", "finance_page", "hr_page"]
        
        events = []
        for i in range(11):
            # Add a 3 second delay before the last event
            delta = i * 1.5 if i < 10 else i * 1.5 + 3.0
            event = AccessEvent(
                user_id=user.id,
                session_id="test_sess_rapid_reset",
                resource=resources[i],
                resource_sensitivity="low",
                timestamp=base_time + timedelta(seconds=delta),
                ip_address="127.0.0.1",
                privilege_mismatch=False
            )
            db.session.add(event)
            db.session.flush()
            events.append(event)
        
        db.session.commit()

        analysis = {
            "prediction": {"predicted_risk": "low", "probability_high": 0.05},
            "anomaly_detection": {"is_anomaly": False, "anomaly_score": -0.1},
            "behavioral_cluster": {"cluster_id": 1, "archetype_name": "normal"},
            "explanation": {}
        }

        result = apply_zero_trust_policy(
            session_id="test_sess_rapid_reset",
            access_event_id=events[10].id,
            analysis=analysis
        )

        assert result["action"] != "Block"
