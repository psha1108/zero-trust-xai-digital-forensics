"""Contract tests for backend Random Forest + SHAP orchestration."""

from __future__ import annotations

import pytest
from ml.explainability.shap.contracts import (
    ShapExplanation,
    ShapFeatureContribution,
)

from app.services.risk_analysis import analyze_operational_access


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
        "ip_changed_during_session": 1,
        "device_changed_during_session": 0,
        "sensitive_resource_access_count": 2,
    }


def test_analysis_uses_exact_same_record_for_rf_and_shap(
    monkeypatch,
) -> None:
    record = _sample_record()

    observed = {
        "builder_calls": 0,
        "rf_record_id": None,
        "shap_record_id": None,
    }

    def fake_builder(*, session_id, access_event_id):
        assert session_id == "session-123"
        assert access_event_id == 42

        observed["builder_calls"] += 1
        return record

    def fake_classifier(sample):
        observed["rf_record_id"] = id(sample)

        assert sample is record

        return {
            "predicted_risk": "high",
            "probability_low": 0.05,
            "probability_medium": 0.10,
            "probability_high": 0.85,
        }

    def fake_explainer(sample, bundle_path=None):
        observed["shap_record_id"] = id(sample)

        assert sample is record
        assert bundle_path is None

        return {
            "explanation": {
                "model": "operational_random_forest",
            },
            "prediction": "high",
            "class_index": 0,
            "class_order": ["high", "low", "medium"],
            "model_probability": 0.85,
            "additivity": {
                "passed": True,
            },
        }

    monkeypatch.setattr(
        "app.services.risk_analysis."
        "build_operational_feature_record_from_database",
        fake_builder,
    )

    monkeypatch.setattr(
        "app.services.risk_analysis."
        "classify_operational_record",
        fake_classifier,
    )

    monkeypatch.setattr(
        "app.services.risk_analysis."
        "explain_random_forest_prediction",
        fake_explainer,
    )

    result = analyze_operational_access(
        session_id="session-123",
        access_event_id=42,
    )

    assert observed["builder_calls"] == 1

    assert observed["rf_record_id"] == id(record)
    assert observed["shap_record_id"] == id(record)
    assert observed["rf_record_id"] == observed["shap_record_id"]

    assert result == {
        "features": record,
        "prediction": {
            "predicted_risk": "high",
            "probability_low": 0.05,
            "probability_medium": 0.10,
            "probability_high": 0.85,
        },
        "explanation": {
            "explanation": {
                "model": "operational_random_forest",
            },
            "prediction": "high",
            "class_index": 0,
            "class_order": ["high", "low", "medium"],
            "model_probability": 0.85,
            "additivity": {
                "passed": True,
            },
        },
    }


def test_analysis_rejects_prediction_explanation_class_mismatch(
    monkeypatch,
) -> None:
    record = _sample_record()

    monkeypatch.setattr(
        "app.services.risk_analysis."
        "build_operational_feature_record_from_database",
        lambda **kwargs: record,
    )

    monkeypatch.setattr(
        "app.services.risk_analysis."
        "classify_operational_record",
        lambda sample: {
            "predicted_risk": "high",
            "probability_low": 0.05,
            "probability_medium": 0.10,
            "probability_high": 0.85,
        },
    )

    monkeypatch.setattr(
        "app.services.risk_analysis."
        "explain_random_forest_prediction",
        lambda sample, bundle_path=None: {
            "explanation": {},
            "prediction": "medium",
            "class_index": 2,
            "class_order": ["high", "low", "medium"],
            "model_probability": 0.60,
            "additivity": {
                "passed": True,
            },
        },
    )

    with pytest.raises(
        ValueError,
        match="prediction/explanation class mismatch",
    ):
        analyze_operational_access(
            session_id="session-123",
            access_event_id=42,
        )


def test_analysis_does_not_return_policy_action(
    monkeypatch,
) -> None:
    record = _sample_record()

    monkeypatch.setattr(
        "app.services.risk_analysis."
        "build_operational_feature_record_from_database",
        lambda **kwargs: record,
    )

    monkeypatch.setattr(
        "app.services.risk_analysis."
        "classify_operational_record",
        lambda sample: {
            "predicted_risk": "low",
            "probability_low": 0.90,
            "probability_medium": 0.08,
            "probability_high": 0.02,
        },
    )

    monkeypatch.setattr(
        "app.services.risk_analysis."
        "explain_random_forest_prediction",
        lambda sample, bundle_path=None: {
            "explanation": {},
            "prediction": "low",
            "class_index": 1,
            "class_order": ["high", "low", "medium"],
            "model_probability": 0.90,
            "additivity": {
                "passed": True,
            },
        },
    )

    result = analyze_operational_access(
        session_id="session-123",
        access_event_id=42,
    )

    assert "action" not in result
    assert "decision" not in result
    assert "policy_action" not in result

def test_analysis_serializes_shap_contract_for_backend(
    monkeypatch,
) -> None:
    record = _sample_record()

    monkeypatch.setattr(
        "app.services.risk_analysis."
        "build_operational_feature_record_from_database",
        lambda **kwargs: record,
    )

    monkeypatch.setattr(
        "app.services.risk_analysis."
        "classify_operational_record",
        lambda sample: {
            "predicted_risk": "medium",
            "probability_low": 0.10,
            "probability_medium": 0.80,
            "probability_high": 0.10,
        },
    )

    shap_contract = ShapExplanation(
        prediction="medium",
        base_value=0.25,
        contributions=(
            ShapFeatureContribution(
                feature_name="failed_attempt_count",
                contribution=0.20,
            ),
            ShapFeatureContribution(
                feature_name="is_new_ip",
                contribution=0.05,
            ),
        ),
    )

    monkeypatch.setattr(
        "app.services.risk_analysis."
        "explain_random_forest_prediction",
        lambda sample, bundle_path=None: {
            "explanation": shap_contract,
            "prediction": "medium",
            "class_index": 2,
            "class_order": ["high", "low", "medium"],
            "model_probability": 0.80,
            "additivity": {
                "base_value": 0.25,
                "contribution_sum": 0.25,
                "reconstructed_output": 0.50,
                "model_output": 0.50,
                "additivity_error": 0.0,
                "is_additive": True,
            },
        },
    )

    result = analyze_operational_access(
        session_id="session-123",
        access_event_id=42,
    )

    serialized = result["explanation"]["explanation"]

    assert serialized == {
        "prediction": "medium",
        "base_value": 0.25,
        "contributions": [
            {
                "feature_name": "failed_attempt_count",
                "contribution": 0.20,
            },
            {
                "feature_name": "is_new_ip",
                "contribution": 0.05,
            },
        ],
    }