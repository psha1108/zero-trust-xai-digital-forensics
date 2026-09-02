"""Backend contract tests for K-Means behavioral integration."""

from __future__ import annotations

from datetime import datetime

import app.services.risk_analysis as risk_analysis
from app.extensions import db
from app.models import AccessEvent, LoginEvent, Session, User


def _sample_record() -> dict[str, object]:
    return {
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
        "ip_changed_during_session": 0,
        "device_changed_during_session": 0,
        "sensitive_resource_access_count": 2,
    }


def _patch_analysis_stack(
    monkeypatch,
    *,
    record: dict[str, object],
    cluster_id: int = 0,
    archetype_name: str = "Elevated Behavioral Activity",
):
    observed = {
        "builder_calls": 0,
        "rf_record_id": None,
        "shap_record_id": None,
        "kmeans_record_id": None,
        "kmeans_calls": 0,
    }

    def fake_builder(*, session_id, access_event_id):
        assert isinstance(session_id, str)
        assert isinstance(access_event_id, int)

        observed["builder_calls"] += 1
        return record

    def fake_classifier(sample):
        observed["rf_record_id"] = id(sample)

        return {
            "predicted_risk": "medium",
            "probability_low": 0.10,
            "probability_medium": 0.80,
            "probability_high": 0.10,
        }

    def fake_explainer(sample, bundle_path=None):
        observed["shap_record_id"] = id(sample)

        assert bundle_path is None

        return {
            "explanation": {},
            "prediction": "medium",
            "class_index": 2,
            "class_order": [
                "high",
                "low",
                "medium",
            ],
            "model_probability": 0.80,
            "additivity": {
                "is_additive": True,
            },
        }

    def fake_clusterer(sample, bundle_path=None):
        observed["kmeans_calls"] += 1
        observed["kmeans_record_id"] = id(sample)

        assert bundle_path is None

        return {
            "cluster_id": cluster_id,
            "archetype_name": archetype_name,
        }

    monkeypatch.setattr(
        risk_analysis,
        "build_operational_feature_record_from_database",
        fake_builder,
    )

    monkeypatch.setattr(
        risk_analysis,
        "classify_operational_record",
        fake_classifier,
    )

    monkeypatch.setattr(
        risk_analysis,
        "explain_random_forest_prediction",
        fake_explainer,
    )

    monkeypatch.setattr(
        risk_analysis,
        "cluster_operational_record",
        fake_clusterer,
        raising=False,
    )

    return observed


def test_rf_shap_and_kmeans_receive_exact_same_feature_record(
    monkeypatch,
) -> None:
    record = _sample_record()

    observed = _patch_analysis_stack(
        monkeypatch,
        record=record,
    )

    result = risk_analysis.analyze_operational_access(
        session_id="session-123",
        access_event_id=42,
    )

    assert observed["builder_calls"] == 1
    assert observed["kmeans_calls"] == 1

    assert observed["rf_record_id"] == id(record)
    assert observed["shap_record_id"] == id(record)
    assert observed["kmeans_record_id"] == id(record)

    assert (
        observed["rf_record_id"]
        == observed["shap_record_id"]
        == observed["kmeans_record_id"]
    )

    assert set(result) == {
        "features",
        "prediction",
        "behavioral_cluster",
        "explanation",
    }

    assert result["behavioral_cluster"] == {
        "cluster_id": 0,
        "archetype_name": "Elevated Behavioral Activity",
    }


def test_kmeans_output_remains_behavioral_and_policy_independent(
    monkeypatch,
) -> None:
    record = _sample_record()

    _patch_analysis_stack(
        monkeypatch,
        record=record,
        cluster_id=1,
        archetype_name="Routine Behavioral Activity",
    )

    result = risk_analysis.analyze_operational_access(
        session_id="session-456",
        access_event_id=77,
    )

    behavioral_cluster = result[
        "behavioral_cluster"
    ]

    assert behavioral_cluster == {
        "cluster_id": 1,
        "archetype_name": "Routine Behavioral Activity",
    }

    assert set(
        behavioral_cluster
    ) == {
        "cluster_id",
        "archetype_name",
    }

    forbidden_policy_fields = {
        "action",
        "decision",
        "policy_action",
        "risk_score",
        "predicted_risk",
        "risk_label",
    }

    assert forbidden_policy_fields.isdisjoint(
        behavioral_cluster
    )

    assert "action" not in result
    assert "decision" not in result
    assert "policy_action" not in result


def test_analysis_persists_canonical_cluster_on_login_event(
    database_app,
    monkeypatch,
) -> None:
    record = _sample_record()

    with database_app.app_context():
        now = datetime(
            2026,
            9,
            2,
            10,
            30,
            0,
        )

        user = User(
            username="kmeans-backend-user",
            email="kmeans-backend-user@example.test",
            password_hash="test-only",
            role="employee",
        )

        db.session.add(user)
        db.session.flush()

        login_event = LoginEvent(
            user_id=user.id,
            username_attempted=user.username,
            timestamp=now,
            ip_address="10.0.0.5",
            device_info="Chrome Windows",
            success=True,
        )

        db.session.add(login_event)
        db.session.flush()

        session = Session(
            session_id="kmeans-persistence-session",
            user_id=user.id,
            login_event_id=login_event.id,
            started_at=now,
            start_ip="10.0.0.5",
            current_ip="10.0.0.5",
            start_device_fingerprint="chrome-windows",
            current_device_fingerprint="chrome-windows",
            is_active=True,
        )

        db.session.add(session)
        db.session.flush()

        access_event = AccessEvent(
            user_id=user.id,
            session_id=session.session_id,
            resource="finance_page",
            resource_sensitivity="high",
            timestamp=now,
            ip_address="10.0.0.5",
            device_fingerprint="chrome-windows",
            privilege_mismatch=False,
            ip_changed=False,
            device_changed=False,
        )

        db.session.add(access_event)
        db.session.commit()

        _patch_analysis_stack(
            monkeypatch,
            record=record,
            cluster_id=0,
            archetype_name="Elevated Behavioral Activity",
        )

        result = risk_analysis.analyze_operational_access(
            session_id=session.session_id,
            access_event_id=access_event.id,
        )

        db.session.expire_all()

        persisted_login_event = db.session.get(
            LoginEvent,
            login_event.id,
        )

        persisted_access_event = db.session.get(
            AccessEvent,
            access_event.id,
        )

        assert persisted_login_event is not None

        assert persisted_login_event.cluster_id == (
            result["behavioral_cluster"]["cluster_id"]
        )

        assert persisted_login_event.cluster_id == 0

        # K-Means must not enforce Zero Trust policy.
        assert persisted_login_event.action_taken is None
        assert persisted_access_event is not None
        assert persisted_access_event.decision is None
        assert persisted_access_event.risk_score is None
