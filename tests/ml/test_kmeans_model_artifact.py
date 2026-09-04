"""Contract tests for the final operational K-Means model artifact."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer

from ml.clustering.preprocessing import (
    EXPECTED_TRANSFORMED_FEATURE_COLUMNS,
    MODEL_FEATURE_COLUMNS,
)
from ml.clustering.train_operational_model import (
    ARCHETYPE_SCORE_FEATURES,
    CANONICAL_ARCHETYPE_NAMES,
    FINAL_DEVELOPMENT_ROWS,
    FINAL_DEVELOPMENT_USERS,
    SELECTED_K,
    build_development_training_frame,
    fit_operational_kmeans,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "ml_training_dataset.csv"
)

SPLIT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "operational"
    / "isolation_forest_split_assignments.csv"
)


def test_final_training_constants_are_frozen() -> None:
    assert SELECTED_K == 2

    assert FINAL_DEVELOPMENT_ROWS == 692
    assert FINAL_DEVELOPMENT_USERS == 40

    assert CANONICAL_ARCHETYPE_NAMES == {
        0: "Elevated Behavioral Activity",
        1: "Routine Behavioral Activity",
    }

    assert ARCHETYPE_SCORE_FEATURES == [
        "failed_attempt_count",
        "sensitive_resource_access_count",
        "access_count_5min",
        "session_duration_minutes",
        "is_unusual_time",
        "resource_sensitivity_score",
        "unauthorized_access_attempt",
    ]


def test_final_training_frame_uses_fit_plus_validation_only() -> None:
    training_df = build_development_training_frame(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    assert len(training_df) == 692

    assert training_df[
        "user_id"
    ].nunique() == 40

    assert set(
        training_df["partition"].unique()
    ) == {
        "fit",
        "validation",
    }

    assert not training_df[
        "partition"
    ].eq("test").any()


def test_final_training_frame_preserves_operational_features() -> None:
    training_df = build_development_training_frame(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    for feature in MODEL_FEATURE_COLUMNS:
        assert feature in training_df.columns

    assert "user_id" in training_df.columns
    assert "risk_label" in training_df.columns
    assert "scenario_type" in training_df.columns

    # These columns may exist for auditability but must never be
    # included in the 14-feature clustering contract.
    assert "user_id" not in MODEL_FEATURE_COLUMNS
    assert "risk_label" not in MODEL_FEATURE_COLUMNS
    assert "scenario_type" not in MODEL_FEATURE_COLUMNS


def test_final_model_bundle_has_exact_contract() -> None:
    bundle, metadata = fit_operational_kmeans(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    assert bundle["artifact_schema_version"] == 1

    assert bundle[
        "model_name"
    ] == "operational_kmeans_behavioral_clustering"

    assert bundle["selected_k"] == 2

    assert isinstance(
        bundle["preprocessor"],
        ColumnTransformer,
    )

    assert isinstance(
        bundle["model"],
        KMeans,
    )

    assert bundle["model"].n_clusters == 2

    assert bundle[
        "source_features"
    ] == MODEL_FEATURE_COLUMNS

    assert bundle[
        "transformed_features"
    ] == EXPECTED_TRANSFORMED_FEATURE_COLUMNS

    assert bundle[
        "canonical_archetype_names"
    ] == CANONICAL_ARCHETYPE_NAMES

    mapping = bundle[
        "native_to_canonical_cluster_id"
    ]

    assert set(mapping.keys()) == {
        0,
        1,
    }

    assert set(mapping.values()) == {
        0,
        1,
    }

    assert metadata["selected_k"] == 2


def test_final_model_uses_all_692_development_rows() -> None:
    bundle, metadata = fit_operational_kmeans(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    model = bundle["model"]

    assert model.n_clusters == 2

    assert metadata[
        "training_partition"
    ] == "fit_plus_validation"

    assert metadata[
        "training_rows"
    ] == 692

    assert metadata[
        "training_users"
    ] == 40

    assert metadata[
        "test_rows_used_for_training"
    ] == 0


def test_final_model_metadata_preserves_unsupervised_semantics() -> None:
    _, metadata = fit_operational_kmeans(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    assert metadata[
        "task"
    ] == "unsupervised_behavioral_clustering"

    assert metadata[
        "risk_label_used_for_training"
    ] is False

    assert metadata[
        "scenario_type_used_for_training"
    ] is False

    assert metadata[
        "test_partition_used_for_training"
    ] is False

    assert metadata[
        "canonical_archetype_names"
    ] == {
        "0": "Elevated Behavioral Activity",
        "1": "Routine Behavioral Activity",
    }

    assert metadata[
        "archetype_semantics"
    ] == (
        "behavioral context only; cluster IDs are not "
        "risk classes or access-control decisions"
    )


def test_semantic_mapping_assigns_higher_activity_centroid_to_cluster_zero() -> None:
    bundle, _ = fit_operational_kmeans(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    model = bundle["model"]

    transformed_features = bundle[
        "transformed_features"
    ]

    mapping = bundle[
        "native_to_canonical_cluster_id"
    ]

    score_indices = [
        transformed_features.index(feature)
        for feature in ARCHETYPE_SCORE_FEATURES
    ]

    native_scores = {}

    for native_cluster_id in range(2):
        centroid = model.cluster_centers_[
            native_cluster_id
        ]

        native_scores[native_cluster_id] = float(
            np.mean(
                centroid[
                    score_indices
                ]
            )
        )

    elevated_native = max(
        native_scores,
        key=native_scores.get,
    )

    routine_native = min(
        native_scores,
        key=native_scores.get,
    )

    assert mapping[elevated_native] == 0
    assert mapping[routine_native] == 1

    assert (
        native_scores[elevated_native]
        > native_scores[routine_native]
    )


def test_final_model_produces_both_behavioral_archetypes() -> None:
    training_df = build_development_training_frame(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    bundle, metadata = fit_operational_kmeans(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    features = training_df[
        MODEL_FEATURE_COLUMNS
    ].copy()

    transformed = bundle[
        "preprocessor"
    ].transform(features)

    transformed = np.asarray(
        transformed,
        dtype=np.float64,
    )

    native_labels = bundle[
        "model"
    ].predict(transformed)

    mapping = bundle[
        "native_to_canonical_cluster_id"
    ]

    canonical_labels = np.array(
        [
            mapping[int(label)]
            for label in native_labels
        ],
        dtype=np.int64,
    )

    assert set(
        np.unique(canonical_labels)
    ) == {
        0,
        1,
    }

    counts = {
        int(cluster_id): int(
            np.sum(
                canonical_labels == cluster_id
            )
        )
        for cluster_id in [0, 1]
    }

    assert counts[0] > 0
    assert counts[1] > 0

    assert sum(counts.values()) == 692

    assert metadata[
        "development_cluster_sizes"
    ] == {
        "0": counts[0],
        "1": counts[1],
    }


def test_final_model_fit_is_semantically_repeatable() -> None:
    first_bundle, first_metadata = fit_operational_kmeans(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    second_bundle, second_metadata = fit_operational_kmeans(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    assert (
        first_bundle[
            "native_to_canonical_cluster_id"
        ]
        == second_bundle[
            "native_to_canonical_cluster_id"
        ]
    )

    assert np.allclose(
        first_bundle[
            "model"
        ].cluster_centers_,
        second_bundle[
            "model"
        ].cluster_centers_,
        rtol=0.0,
        atol=1e-10,
    )

    assert (
        first_metadata[
            "development_cluster_sizes"
        ]
        == second_metadata[
            "development_cluster_sizes"
        ]
    )
