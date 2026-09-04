"""Contract tests for operational K-Means inference."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.clustering.inference import (
    cluster_operational_record,
    cluster_operational_records,
)
from ml.clustering.persist_operational_model import (
    load_operational_kmeans_bundle,
)
from ml.clustering.preprocessing import (
    MODEL_FEATURE_COLUMNS,
    select_kmeans_features,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ARTIFACT_PATH = (
    PROJECT_ROOT
    / "model_artifacts"
    / "operational"
    / "kmeans_behavioral_bundle.joblib"
)


ROUTINE_SAMPLE = {
    "role": "employee",
    "login_hour": 11,
    "is_working_hour": 1,
    "failed_attempt_count": 0,
    "is_new_ip": 0,
    "is_new_device": 0,
    "is_unusual_time": 0,
    "session_duration_minutes": 25.0,
    "resource_sensitivity_score": 1,
    "access_count_5min": 2,
    "unauthorized_access_attempt": 0,
    "ip_changed_during_session": 0,
    "device_changed_during_session": 0,
    "sensitive_resource_access_count": 0,
}


ELEVATED_SAMPLE = {
    "role": "guest",
    "login_hour": 2,
    "is_working_hour": 0,
    "failed_attempt_count": 9,
    "is_new_ip": 1,
    "is_new_device": 1,
    "is_unusual_time": 1,
    "session_duration_minutes": 250.0,
    "resource_sensitivity_score": 4,
    "access_count_5min": 30,
    "unauthorized_access_attempt": 1,
    "ip_changed_during_session": 1,
    "device_changed_during_session": 1,
    "sensitive_resource_access_count": 15,
}


def test_single_record_returns_exact_behavioral_contract() -> None:
    result = cluster_operational_record(
        ROUTINE_SAMPLE
    )

    assert set(result) == {
        "cluster_id",
        "archetype_name",
    }

    assert result["cluster_id"] in {
        0,
        1,
    }

    assert result["archetype_name"] in {
        "Elevated Behavioral Activity",
        "Routine Behavioral Activity",
    }


def test_single_record_matches_frozen_bundle_prediction() -> None:
    bundle = load_operational_kmeans_bundle(
        ARTIFACT_PATH
    )

    frame = select_kmeans_features(
        pd.DataFrame(
            [ROUTINE_SAMPLE],
            columns=MODEL_FEATURE_COLUMNS,
        )
    )

    transformed = np.asarray(
        bundle["preprocessor"].transform(
            frame
        ),
        dtype=np.float64,
    )

    native_cluster_id = int(
        bundle["model"].predict(
            transformed
        )[0]
    )

    canonical_cluster_id = int(
        bundle[
            "native_to_canonical_cluster_id"
        ][native_cluster_id]
    )

    expected_name = bundle[
        "canonical_archetype_names"
    ][canonical_cluster_id]

    result = cluster_operational_record(
        ROUTINE_SAMPLE
    )

    assert (
        result["cluster_id"]
        == canonical_cluster_id
    )

    assert (
        result["archetype_name"]
        == expected_name
    )


def test_batch_inference_preserves_input_order() -> None:
    records = [
        ROUTINE_SAMPLE,
        ELEVATED_SAMPLE,
        ROUTINE_SAMPLE,
    ]

    results = cluster_operational_records(
        records
    )

    assert len(results) == 3

    assert results[0] == (
        cluster_operational_record(
            ROUTINE_SAMPLE
        )
    )

    assert results[1] == (
        cluster_operational_record(
            ELEVATED_SAMPLE
        )
    )

    assert results[2] == (
        cluster_operational_record(
            ROUTINE_SAMPLE
        )
    )


def test_canonical_names_are_consistent_with_cluster_ids() -> None:
    results = cluster_operational_records(
        [
            ROUTINE_SAMPLE,
            ELEVATED_SAMPLE,
        ]
    )

    expected_names = {
        0: "Elevated Behavioral Activity",
        1: "Routine Behavioral Activity",
    }

    for result in results:
        assert (
            result["archetype_name"]
            == expected_names[
                result["cluster_id"]
            ]
        )


def test_inference_is_deterministic() -> None:
    first = cluster_operational_records(
        [
            ROUTINE_SAMPLE,
            ELEVATED_SAMPLE,
        ]
    )

    second = cluster_operational_records(
        [
            ROUTINE_SAMPLE,
            ELEVATED_SAMPLE,
        ]
    )

    assert first == second


def test_inference_does_not_return_risk_or_policy_fields() -> None:
    result = cluster_operational_record(
        ELEVATED_SAMPLE
    )

    forbidden_fields = {
        "risk",
        "risk_label",
        "risk_score",
        "predicted_risk",
        "decision",
        "action",
        "action_taken",
        "policy",
    }

    assert forbidden_fields.isdisjoint(
        result.keys()
    )


def test_missing_operational_feature_is_rejected() -> None:
    incomplete = dict(
        ROUTINE_SAMPLE
    )

    incomplete.pop(
        "access_count_5min"
    )

    with pytest.raises(
        ValueError,
        match="missing|required",
    ):
        cluster_operational_record(
            incomplete
        )


def test_unknown_role_is_rejected() -> None:
    invalid = dict(
        ROUTINE_SAMPLE
    )

    invalid["role"] = (
        "superuser"
    )

    with pytest.raises(
        ValueError,
        match="role|unknown",
    ):
        cluster_operational_record(
            invalid
        )


def test_exact_14_source_features_are_used() -> None:
    assert len(
        MODEL_FEATURE_COLUMNS
    ) == 14

    assert set(
        ROUTINE_SAMPLE
    ) == set(
        MODEL_FEATURE_COLUMNS
    )

    assert "user_id" not in MODEL_FEATURE_COLUMNS
    assert "risk_label" not in MODEL_FEATURE_COLUMNS
    assert "scenario_type" not in MODEL_FEATURE_COLUMNS


def test_empty_batch_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="empty|at least one",
    ):
        cluster_operational_records(
            []
        )
