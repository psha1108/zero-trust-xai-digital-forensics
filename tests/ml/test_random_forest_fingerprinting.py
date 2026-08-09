"""Tests for Random Forest semantic fingerprinting."""

from __future__ import annotations

import copy

import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier

from ml.classification.fingerprinting import (
    calculate_random_forest_semantic_fingerprint,
)


def build_fixture_bundle() -> dict:
    """Create a tiny deterministic classifier fixture."""

    X = np.asarray(
        [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [2.0, 0.0],
            [2.0, 1.0],
        ],
        dtype=np.float64,
    )

    y = np.asarray(
        [
            "low",
            "low",
            "medium",
            "medium",
            "high",
            "high",
        ],
    )

    model = RandomForestClassifier(
        n_estimators=5,
        criterion="gini",
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features="sqrt",
        bootstrap=True,
        class_weight=None,
        random_state=42,
        n_jobs=1,
    )

    model.fit(
        X,
        y,
    )

    return {
        "artifact_schema_version": 1,
        "model_name": "operational_random_forest",
        "model_type": "RandomForestClassifier",
        "selected_candidate_id": "rf_baseline",
        "source_feature_columns": [
            "feature_a",
            "feature_b",
        ],
        "transformed_feature_columns": [
            "feature_a",
            "feature_b",
        ],
        "transformed_source_feature_mapping": {
            "feature_a": "feature_a",
            "feature_b": "feature_b",
        },
        "role_categories": [
            "admin",
            "employee",
            "finance_user",
            "guest",
            "hr_user",
        ],
        "class_order": (
            model.classes_
            .astype(str)
            .tolist()
        ),
        "model_parameters": {
            "n_estimators": 5,
            "criterion": "gini",
            "max_depth": None,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
            "max_features": "sqrt",
            "bootstrap": True,
            "class_weight": None,
            "random_state": 42,
            "n_jobs": 1,
        },
        "model": model,
    }


def test_semantic_fingerprint_is_deterministic() -> None:
    """Equivalent frozen model state must reproduce the same fingerprint."""

    first_bundle = build_fixture_bundle()
    second_bundle = build_fixture_bundle()

    first = (
        calculate_random_forest_semantic_fingerprint(
            first_bundle
        )
    )

    second = (
        calculate_random_forest_semantic_fingerprint(
            second_bundle
        )
    )

    assert len(first) == 64
    assert first == second


def test_feature_contract_change_changes_fingerprint() -> None:
    """Feature-contract changes must alter semantic identity."""

    bundle = build_fixture_bundle()

    original = (
        calculate_random_forest_semantic_fingerprint(
            bundle
        )
    )

    changed = copy.copy(
        bundle
    )

    changed[
        "source_feature_columns"
    ] = [
        "feature_b",
        "feature_a",
    ]

    assert (
        calculate_random_forest_semantic_fingerprint(
            changed
        )
        != original
    )


def test_parameter_contract_change_changes_fingerprint() -> None:
    """Stored model-parameter changes must alter semantic identity."""

    bundle = build_fixture_bundle()

    original = (
        calculate_random_forest_semantic_fingerprint(
            bundle
        )
    )

    changed = copy.copy(
        bundle
    )

    changed_parameters = dict(
        bundle[
            "model_parameters"
        ]
    )

    changed_parameters[
        "max_depth"
    ] = 12

    changed[
        "model_parameters"
    ] = changed_parameters

    assert (
        calculate_random_forest_semantic_fingerprint(
            changed
        )
        != original
    )


def test_class_order_mismatch_is_rejected() -> None:
    """Stored probability order must agree with model.classes_."""

    bundle = build_fixture_bundle()

    bundle[
        "class_order"
    ] = [
        "low",
        "medium",
        "high",
    ]

    with pytest.raises(
        ValueError,
        match="class order",
    ):
        calculate_random_forest_semantic_fingerprint(
            bundle
        )


def test_missing_contract_field_is_rejected() -> None:
    """Incomplete artifact contracts must not be fingerprinted."""

    bundle = build_fixture_bundle()

    del bundle[
        "selected_candidate_id"
    ]

    with pytest.raises(
        ValueError,
        match="missing fields",
    ):
        calculate_random_forest_semantic_fingerprint(
            bundle
        )
