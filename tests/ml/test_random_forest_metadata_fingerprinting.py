"""Tests for Random Forest metadata semantic fingerprinting."""

from __future__ import annotations

import copy

import pytest

from ml.classification.fingerprinting import (
    calculate_random_forest_metadata_semantic_fingerprint,
)


def build_metadata_fixture() -> dict:
    """Return a representative frozen RF metadata contract."""

    return {
        "metadata_schema_version": 1,
        "model_name": "operational_random_forest",
        "model_type": "RandomForestClassifier",
        "artifact_filename": "random_forest_risk_bundle.joblib",
        "artifact_sha256": "a" * 64,
        "semantic_fingerprint": "b" * 64,
        "reproducibility_definition": (
            "semantic model structure, feature contract, "
            "class order and predictions"
        ),
        "dataset_filename": "ml_training_dataset.csv",
        "dataset_canonical_sha256": "c" * 64,
        "assignment_filename": (
            "isolation_forest_split_assignments.csv"
        ),
        "assignment_canonical_sha256": "d" * 64,
        "selection_filename": (
            "operational_random_forest_selection.json"
        ),
        "selection_canonical_sha256": "e" * 64,
        "training_scope": (
            "all labeled records from fit and validation "
            "partitions"
        ),
        "development_rows": 692,
        "development_users": 40,
        "development_label_counts": {
            "low": 452,
            "medium": 162,
            "high": 78,
        },
        "source_feature_count": 14,
        "transformed_feature_count": 18,
        "source_feature_columns": [
            "role",
            "login_hour",
        ],
        "transformed_feature_columns": [
            "role_admin",
            "login_hour",
        ],
        "transformed_source_feature_mapping": {
            "role_admin": "role",
            "login_hour": "login_hour",
        },
        "role_categories": [
            "admin",
            "employee",
            "finance_user",
            "guest",
            "hr_user",
        ],
        "selected_candidate_id": "rf_baseline",
        "model_parameters": {
            "n_estimators": 300,
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
        "class_order": [
            "high",
            "low",
            "medium",
        ],
        "class_to_index": {
            "high": 0,
            "low": 1,
            "medium": 2,
        },
        "report_label_order": [
            "low",
            "medium",
            "high",
        ],
        "software_versions": {
            "scikit_learn": "1.5.1",
        },
    }


def test_metadata_fingerprint_is_deterministic() -> None:
    """Equivalent metadata must produce identical identity."""

    first = build_metadata_fixture()

    second = dict(
        reversed(
            list(
                build_metadata_fixture().items()
            )
        )
    )

    assert (
        calculate_random_forest_metadata_semantic_fingerprint(
            first
        )
        ==
        calculate_random_forest_metadata_semantic_fingerprint(
            second
        )
    )


def test_semantic_metadata_change_changes_fingerprint() -> None:
    """A class-contract change must alter metadata identity."""

    metadata = build_metadata_fixture()

    original = (
        calculate_random_forest_metadata_semantic_fingerprint(
            metadata
        )
    )

    changed = copy.deepcopy(
        metadata
    )

    changed[
        "class_order"
    ] = [
        "low",
        "medium",
        "high",
    ]

    assert (
        calculate_random_forest_metadata_semantic_fingerprint(
            changed
        )
        != original
    )


def test_artifact_byte_checksum_is_not_semantic_metadata() -> None:
    """Joblib byte-hash changes must not alter semantic identity."""

    metadata = build_metadata_fixture()

    original = (
        calculate_random_forest_metadata_semantic_fingerprint(
            metadata
        )
    )

    changed = copy.deepcopy(
        metadata
    )

    changed[
        "artifact_sha256"
    ] = "f" * 64

    assert (
        calculate_random_forest_metadata_semantic_fingerprint(
            changed
        )
        == original
    )


def test_software_version_is_not_semantic_metadata() -> None:
    """Provenance version changes are outside metadata semantics."""

    metadata = build_metadata_fixture()

    original = (
        calculate_random_forest_metadata_semantic_fingerprint(
            metadata
        )
    )

    changed = copy.deepcopy(
        metadata
    )

    changed[
        "software_versions"
    ] = {
        "scikit_learn": "different-version",
    }

    assert (
        calculate_random_forest_metadata_semantic_fingerprint(
            changed
        )
        == original
    )


def test_missing_metadata_contract_field_is_rejected() -> None:
    """Incomplete RF metadata must not receive a fingerprint."""

    metadata = build_metadata_fixture()

    del metadata[
        "selection_canonical_sha256"
    ]

    with pytest.raises(
        ValueError,
        match="missing fields",
    ):
        calculate_random_forest_metadata_semantic_fingerprint(
            metadata
        )
