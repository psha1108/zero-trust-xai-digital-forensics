"""Contract for unified Isolation Forest + RF + SHAP + K-Means analysis."""

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


def _patch_full_stack(
    monkeypatch,
    *,
    record: dict[str, object],
):
    observed = {
        "builder_calls": 0,
        "if_calls": 0,
        "rf_calls": 0,
        "shap_calls": 0,
        "kmeans_calls": 0,
        "if_record_id": None,
        "rf_record_id": None,
        "shap_record_id": None,
        "kmeans_record_id": None,
    }

    def fake_builder(*, session_id, access_event_id):
        assert isinstance(session_id, str)
        assert isinstance(access_event_id, int)

        observed["builder_calls"] += 1
        return record

    def fake_anomaly_detector(
        sample,
        *,
        artifact_bundle=None,
        model_path=None,
    ):
        observed["if_calls"] += 1
        observed["if_record_id"] = id(sample)

        assert sample is record

        return {
            "anomaly_score": 0.61,
            "anomaly_threshold": 0.5532259181941123,
            "threshold_margin": (
                0.61 - 0.5532259181941123
            ),
            "is_anomaly": True,
        }

    def fake_classifier(sample):
        observed["rf_calls"] += 1
        observed["rf_record_id"] = id(sample)

        assert sample is record

        return {
            "predicted_risk": "medium",
            "probability_low": 0.10,
            "probability_medium": 0.80,
            "probability_high": 0.10,
        }

    def fake_explainer(sample, bundle_path=None):
        observed["shap_calls"] += 1
        observed["shap_record_id"] = id(sample)

        assert sample is record
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

        assert sample is record
        assert bundle_path is None

        return {
            "cluster_id": 0,
            "archetype_name": (
                "Elevated Behavioral Activity"
            ),
        }

    monkeypatch.setattr(
        risk_analysis,
        "build_operational_feature_record_from_database",
        fake_builder,
    )

    monkeypatch.setattr(
        risk_analysis,
        "score_operational_record",
        fake_anomaly_detector,
        raising=False,
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
    )

    return observed


def test_all_models_receive_exact_same_feature_dictionary(
    monkeypatch,
) -> None:
    record = _sample_record()

    observed = _patch_full_stack(
        monkeypatch,
        record=record,
    )

    result = risk_analysis.analyze_operational_access(
        session_id="unified-session",
        access_event_id=42,
    )

    assert observed["builder_calls"] == 1
    assert observed["if_calls"] == 1
    assert observed["rf_calls"] == 1
    assert observed["shap_calls"] == 1
    assert observed["kmeans_calls"] == 1

    expected_id = id(record)

    assert observed["if_record_id"] == expected_id
    assert observed["rf_record_id"] == expected_id
    assert observed["shap_record_id"] == expected_id
    assert observed["kmeans_record_id"] == expected_id

    assert set(result) == {
        "features",
        "anomaly_detection",
        "prediction",
        "behavioral_cluster",
        "explanation",
    }


def test_unified_analysis_returns_separate_model_outputs(
    monkeypatch,
) -> None:
    record = _sample_record()

    _patch_full_stack(
        monkeypatch,
        record=record,
    )

    result = risk_analysis.analyze_operational_access(
        session_id="unified-session",
        access_event_id=42,
    )

    assert result["anomaly_detection"] == {
        "anomaly_score": 0.61,
        "anomaly_threshold": 0.5532259181941123,
        "threshold_margin": (
            0.61 - 0.5532259181941123
        ),
        "is_anomaly": True,
    }

    assert result["prediction"]["predicted_risk"] == (
        "medium"
    )

    assert result["behavioral_cluster"] == {
        "cluster_id": 0,
        "archetype_name": (
            "Elevated Behavioral Activity"
        ),
    }

    assert result["explanation"]["prediction"] == (
        "medium"
    )

    # ML outputs remain evidence/context.
    # Policy enforcement is a later phase.
    assert "action" not in result
    assert "decision" not in result
    assert "policy_action" not in result


def test_unified_analysis_persists_model_results_without_policy(
    database_app,
    monkeypatch,
) -> None:
    record = _sample_record()

    with database_app.app_context():
        now = datetime(
            2026,
            9,
            2,
            11,
            0,
            0,
        )

        user = User(
            username="unified-ml-user",
            email="unified-ml-user@example.test",
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
            session_id="unified-db-session",
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

        _patch_full_stack(
            monkeypatch,
            record=record,
        )

        result = risk_analysis.analyze_operational_access(
            session_id=session.session_id,
            access_event_id=access_event.id,
        )

        db.session.expire_all()

        persisted_login = db.session.get(
            LoginEvent,
            login_event.id,
        )

        persisted_access = db.session.get(
            AccessEvent,
            access_event.id,
        )

        assert persisted_login is not None
        assert persisted_access is not None

        assert persisted_login.anomaly_score == (
            result["anomaly_detection"]["anomaly_score"]
        )

        assert persisted_login.risk_label == (
            result["prediction"]["predicted_risk"]
        )

        assert persisted_login.cluster_id == (
            result["behavioral_cluster"]["cluster_id"]
        )

        # Models must not directly enforce policy.
        assert persisted_login.action_taken is None
        assert persisted_access.decision is None
        assert persisted_access.risk_score is None
