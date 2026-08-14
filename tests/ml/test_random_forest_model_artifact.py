"""Tests for the final operational Random Forest artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pytest
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    log_loss,
)

from ml.classification.data import (
    ASSIGNMENT_PATH,
    DATASET_PATH,
    EXPECTED_ASSIGNMENT_CANONICAL_SHA256,
    EXPECTED_DATASET_CANONICAL_SHA256,
    calculate_canonical_text_sha256,
    load_random_forest_development_data,
)
from ml.classification.fingerprinting import (
    calculate_random_forest_metadata_semantic_fingerprint,
    calculate_random_forest_semantic_fingerprint,
)
from ml.classification.preprocessing import (
    MODEL_FEATURE_COLUMNS,
    ROLE_CATEGORIES,
    get_transformed_feature_names,
    get_transformed_source_feature_mapping,
    transform_random_forest_features,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "model_artifacts"
    / "operational"
    / "random_forest_risk_bundle.joblib"
)

METADATA_PATH = (
    PROJECT_ROOT
    / "model_artifacts"
    / "operational"
    / "random_forest_risk_metadata.json"
)

SELECTION_PATH = (
    PROJECT_ROOT
    / "results"
    / "metrics"
    / "operational_random_forest_selection.json"
)

EXPECTED_MODEL_SEMANTIC_FINGERPRINT = (
    "afc34ff1b02b200b6af25ac18fbda5730"
    "86c337b26b53558bf74cbc5c4cc5824"
)

EXPECTED_METADATA_SEMANTIC_FINGERPRINT = (
    "c92696b0db0b57e2a6f0ff472ca84cdb"
    "9af287290f6762803dbee3e7156647b2"
)

EXPECTED_SELECTION_CANONICAL_SHA256 = (
    "da1be58595d7605aabc66459e18fc01e"
    "346d944086a4d63219ccb7e5a660014c"
)

EXPECTED_CLASS_ORDER = [
    "high",
    "low",
    "medium",
]

REPORT_LABEL_ORDER = [
    "low",
    "medium",
    "high",
]


def calculate_sha256(
    path: Path,
) -> str:
    """Return raw file SHA-256."""

    digest = hashlib.sha256()

    with path.open("rb") as file_handle:
        for block in iter(
            lambda: file_handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


@pytest.fixture(scope="module")
def artifact_bundle() -> dict:
    """Load the saved Random Forest artifact once."""

    return joblib.load(
        MODEL_PATH
    )


@pytest.fixture(scope="module")
def metadata() -> dict:
    """Load the saved Random Forest metadata once."""

    return json.loads(
        METADATA_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_random_forest_artifact_files_exist() -> None:
    """Final model and metadata files must exist."""

    assert MODEL_PATH.is_file()
    assert METADATA_PATH.is_file()

    assert MODEL_PATH.stat().st_size > 0
    assert METADATA_PATH.stat().st_size > 0


def test_metadata_matches_current_artifact_checksum(
    metadata: dict,
) -> None:
    """Metadata must identify the exact saved artifact."""

    assert metadata[
        "artifact_filename"
    ] == MODEL_PATH.name

    assert metadata[
        "artifact_sha256"
    ] == calculate_sha256(
        MODEL_PATH
    )


def test_artifact_schema_and_identity(
    artifact_bundle: dict,
    metadata: dict,
) -> None:
    """Artifact and metadata identities must remain frozen."""

    assert artifact_bundle[
        "artifact_schema_version"
    ] == 1

    assert metadata[
        "metadata_schema_version"
    ] == 1

    assert artifact_bundle[
        "model_name"
    ] == "operational_random_forest"

    assert artifact_bundle[
        "model_type"
    ] == "RandomForestClassifier"

    assert metadata[
        "model_name"
    ] == artifact_bundle[
        "model_name"
    ]

    assert metadata[
        "model_type"
    ] == artifact_bundle[
        "model_type"
    ]

    assert artifact_bundle[
        "selected_candidate_id"
    ] == "rf_baseline"

    assert metadata[
        "selected_candidate_id"
    ] == "rf_baseline"


def test_selected_model_parameters(
    artifact_bundle: dict,
    metadata: dict,
) -> None:
    """The frozen selected RF configuration must be preserved."""

    expected_parameters = {
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
    }

    assert artifact_bundle[
        "model_parameters"
    ] == expected_parameters

    assert metadata[
        "model_parameters"
    ] == expected_parameters

    model = artifact_bundle[
        "model"
    ]

    assert len(
        model.estimators_
    ) == 300

    assert (
        np.asarray(
            model.classes_
        )
        .astype(str)
        .tolist()
        ==
        EXPECTED_CLASS_ORDER
    )


def test_semantic_fingerprint_contract(
    artifact_bundle: dict,
    metadata: dict,
) -> None:
    """Model and metadata semantic identities must remain stable."""

    calculated_model_fingerprint = (
        calculate_random_forest_semantic_fingerprint(
            artifact_bundle
        )
    )

    assert (
        calculated_model_fingerprint
        ==
        EXPECTED_MODEL_SEMANTIC_FINGERPRINT
    )

    assert artifact_bundle[
        "semantic_fingerprint"
    ] == calculated_model_fingerprint

    assert metadata[
        "semantic_fingerprint"
    ] == calculated_model_fingerprint

    calculated_metadata_fingerprint = (
        calculate_random_forest_metadata_semantic_fingerprint(
            metadata
        )
    )

    assert (
        calculated_metadata_fingerprint
        ==
        EXPECTED_METADATA_SEMANTIC_FINGERPRINT
    )

    assert metadata[
        "metadata_semantic_fingerprint"
    ] == calculated_metadata_fingerprint


def test_feature_and_class_contract(
    artifact_bundle: dict,
    metadata: dict,
) -> None:
    """Production feature and probability contracts must stay frozen."""

    assert artifact_bundle[
        "source_feature_columns"
    ] == list(
        MODEL_FEATURE_COLUMNS
    )

    assert artifact_bundle[
        "role_categories"
    ] == list(
        ROLE_CATEGORIES
    )

    assert len(
        artifact_bundle[
            "source_feature_columns"
        ]
    ) == 14

    assert len(
        artifact_bundle[
            "transformed_feature_columns"
        ]
    ) == 18

    assert artifact_bundle[
        "class_order"
    ] == EXPECTED_CLASS_ORDER

    assert metadata[
        "class_order"
    ] == EXPECTED_CLASS_ORDER

    assert metadata[
        "class_to_index"
    ] == {
        "high": 0,
        "low": 1,
        "medium": 2,
    }

    assert metadata[
        "report_label_order"
    ] == REPORT_LABEL_ORDER

    actual_transformed_names = (
        get_transformed_feature_names(
            artifact_bundle[
                "preprocessor"
            ]
        )
    )

    assert (
        actual_transformed_names
        ==
        artifact_bundle[
            "transformed_feature_columns"
        ]
    )

    actual_mapping = (
        get_transformed_source_feature_mapping(
            artifact_bundle[
                "preprocessor"
            ]
        )
    )

    assert (
        actual_mapping
        ==
        artifact_bundle[
            "transformed_source_feature_mapping"
        ]
    )

    assert metadata[
        "transformed_source_feature_mapping"
    ] == actual_mapping


def test_training_provenance_contract(
    metadata: dict,
) -> None:
    """Dataset, split and selection provenance must remain frozen."""

    assert (
        calculate_canonical_text_sha256(
            DATASET_PATH
        )
        ==
        EXPECTED_DATASET_CANONICAL_SHA256
    )

    assert (
        calculate_canonical_text_sha256(
            ASSIGNMENT_PATH
        )
        ==
        EXPECTED_ASSIGNMENT_CANONICAL_SHA256
    )

    assert (
        calculate_canonical_text_sha256(
            SELECTION_PATH
        )
        ==
        EXPECTED_SELECTION_CANONICAL_SHA256
    )

    assert metadata[
        "dataset_canonical_sha256"
    ] == EXPECTED_DATASET_CANONICAL_SHA256

    assert metadata[
        "assignment_canonical_sha256"
    ] == EXPECTED_ASSIGNMENT_CANONICAL_SHA256

    assert metadata[
        "selection_canonical_sha256"
    ] == EXPECTED_SELECTION_CANONICAL_SHA256

    assert metadata[
        "development_rows"
    ] == 692

    assert metadata[
        "development_users"
    ] == 40

    assert metadata[
        "development_label_counts"
    ] == {
        "low": 452,
        "medium": 162,
        "high": 78,
    }

    assert metadata[
        "training_scope"
    ] == (
        "all labeled records from fit and "
        "validation partitions"
    )

    assert metadata[
        "final_test_accessed"
    ] is False


def test_development_prediction_round_trip(
    artifact_bundle: dict,
    metadata: dict,
) -> None:
    """Loaded artifact must reproduce development predictions."""

    development_df = (
        load_random_forest_development_data()
    )

    assert len(
        development_df
    ) == 692

    assert set(
        development_df[
            "partition"
        ]
    ) == {
        "fit",
        "validation",
    }

    transformed_matrix = (
        transform_random_forest_features(
            artifact_bundle[
                "preprocessor"
            ],
            development_df,
        )
    )

    assert transformed_matrix.shape == (
        692,
        18,
    )

    assert transformed_matrix.dtype == (
        np.float64
    )

    assert np.isfinite(
        transformed_matrix
    ).all()

    model = artifact_bundle[
        "model"
    ]

    predictions = (
        np.asarray(
            model.predict(
                transformed_matrix
            )
        )
        .astype(str)
    )

    probabilities = np.asarray(
        model.predict_proba(
            transformed_matrix
        ),
        dtype=np.float64,
    )

    assert predictions.shape == (
        692,
    )

    assert probabilities.shape == (
        692,
        3,
    )

    assert np.isfinite(
        probabilities
    ).all()

    np.testing.assert_allclose(
        probabilities.sum(
            axis=1
        ),
        np.ones(
            692,
            dtype=np.float64,
        ),
        rtol=0.0,
        atol=1e-12,
    )

    targets = (
        development_df[
            "risk_label"
        ]
        .astype(str)
        .to_numpy()
    )

    class_order = artifact_bundle[
        "class_order"
    ]

    calculated_metrics = {
        "accuracy": float(
            accuracy_score(
                targets,
                predictions,
            )
        ),
        "balanced_accuracy": float(
            balanced_accuracy_score(
                targets,
                predictions,
            )
        ),
        "macro_f1": float(
            f1_score(
                targets,
                predictions,
                labels=REPORT_LABEL_ORDER,
                average="macro",
                zero_division=0,
            )
        ),
        "weighted_f1": float(
            f1_score(
                targets,
                predictions,
                labels=REPORT_LABEL_ORDER,
                average="weighted",
                zero_division=0,
            )
        ),
        "log_loss": float(
            log_loss(
                targets,
                probabilities,
                labels=class_order,
            )
        ),
    }

    expected_metrics = metadata[
        "development_training_metrics"
    ]

    for metric_name in [
        "accuracy",
        "balanced_accuracy",
        "macro_f1",
        "weighted_f1",
        "log_loss",
    ]:
        assert calculated_metrics[
            metric_name
        ] == pytest.approx(
            expected_metrics[
                metric_name
            ],
            rel=0.0,
            abs=1e-15,
        )

    assert calculated_metrics[
        "accuracy"
    ] == 1.0

    assert calculated_metrics[
        "balanced_accuracy"
    ] == 1.0

    assert calculated_metrics[
        "macro_f1"
    ] == 1.0

    assert calculated_metrics[
        "weighted_f1"
    ] == 1.0

    assert calculated_metrics[
        "log_loss"
    ] == pytest.approx(
        0.027718393053,
        rel=0.0,
        abs=1e-12,
    )
