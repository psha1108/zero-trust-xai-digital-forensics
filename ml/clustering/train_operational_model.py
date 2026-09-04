"""Final development trainer for operational K-Means clustering."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd

from ml.clustering.preprocessing import (
    EXPECTED_TRANSFORMED_FEATURE_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    build_kmeans_preprocessor,
    get_transformed_feature_names,
    select_kmeans_features,
)
from ml.clustering.selection import (
    KMEANS_ALGORITHM,
    KMEANS_N_INIT,
    KMEANS_RANDOM_STATE,
    build_kmeans_candidate,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "ml_training_dataset.csv"
)

DEFAULT_SPLIT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "operational"
    / "isolation_forest_split_assignments.csv"
)


SELECTED_K: Final[int] = 2

FINAL_DEVELOPMENT_ROWS: Final[int] = 692
FINAL_DEVELOPMENT_USERS: Final[int] = 40

EXPECTED_FIT_ROWS: Final[int] = 554
EXPECTED_VALIDATION_ROWS: Final[int] = 138


CANONICAL_ARCHETYPE_NAMES: Final[dict[int, str]] = {
    0: "Elevated Behavioral Activity",
    1: "Routine Behavioral Activity",
}


ARCHETYPE_SCORE_FEATURES: Final[list[str]] = [
    "failed_attempt_count",
    "sensitive_resource_access_count",
    "access_count_5min",
    "session_duration_minutes",
    "is_unusual_time",
    "resource_sensitivity_score",
    "unauthorized_access_attempt",
]


ARCHETYPE_SEMANTICS: Final[str] = (
    "behavioral context only; cluster IDs are not "
    "risk classes or access-control decisions"
)


def _validate_dataset_split_alignment(
    dataset: pd.DataFrame,
    assignments: pd.DataFrame,
) -> None:
    """Validate frozen operational dataset/split row identity."""

    if len(dataset) != 845:
        raise ValueError(
            "Unexpected operational dataset row count: "
            f"{len(dataset)}"
        )

    if len(assignments) != 845:
        raise ValueError(
            "Unexpected operational split row count: "
            f"{len(assignments)}"
        )

    required_assignment_columns = {
        "source_row_index",
        "user_id",
        "role",
        "risk_label",
        "scenario_type",
        "partition",
    }

    missing = sorted(
        required_assignment_columns
        - set(assignments.columns)
    )

    if missing:
        raise ValueError(
            "Split assignments are missing required columns: "
            + ", ".join(missing)
        )

    expected_source_indices = np.arange(
        len(dataset),
        dtype=np.int64,
    )

    actual_source_indices = pd.to_numeric(
        assignments["source_row_index"],
        errors="raise",
    ).to_numpy(dtype=np.int64)

    if not np.array_equal(
        expected_source_indices,
        actual_source_indices,
    ):
        raise ValueError(
            "Operational dataset rows do not align with "
            "source_row_index."
        )

    for column in [
        "user_id",
        "role",
        "risk_label",
        "scenario_type",
    ]:
        if column not in dataset.columns:
            raise ValueError(
                f"Operational dataset is missing {column}."
            )

        if not dataset[
            column
        ].astype(str).equals(
            assignments[column].astype(str)
        ):
            raise ValueError(
                "Dataset/split row identity mismatch for "
                f"{column}."
            )


def build_development_training_frame(
    *,
    dataset_path: Path = DEFAULT_DATASET_PATH,
    split_path: Path = DEFAULT_SPLIT_PATH,
) -> pd.DataFrame:
    """
    Build the frozen fit+validation development training frame.

    The final held-out test partition is excluded from the returned
    frame and cannot participate in preprocessing or model fitting.
    """

    dataset_path = Path(dataset_path)
    split_path = Path(split_path)

    dataset = pd.read_csv(
        dataset_path
    )

    assignments = pd.read_csv(
        split_path
    )

    _validate_dataset_split_alignment(
        dataset,
        assignments,
    )

    development_mask = assignments[
        "partition"
    ].isin(
        [
            "fit",
            "validation",
        ]
    )

    training_df = dataset.loc[
        development_mask
    ].copy()

    training_df["partition"] = (
        assignments.loc[
            development_mask,
            "partition",
        ]
        .to_numpy()
    )

    if len(training_df) != FINAL_DEVELOPMENT_ROWS:
        raise ValueError(
            "Unexpected development training rows: "
            f"{len(training_df)}"
        )

    training_users = int(
        training_df[
            "user_id"
        ].nunique()
    )

    if training_users != FINAL_DEVELOPMENT_USERS:
        raise ValueError(
            "Unexpected development training users: "
            f"{training_users}"
        )

    partition_counts = (
        training_df[
            "partition"
        ]
        .value_counts()
        .to_dict()
    )

    if partition_counts != {
        "fit": EXPECTED_FIT_ROWS,
        "validation": EXPECTED_VALIDATION_ROWS,
    }:
        raise ValueError(
            "Unexpected development partition counts: "
            f"{partition_counts}"
        )

    if training_df[
        "partition"
    ].eq(
        "test"
    ).any():
        raise ValueError(
            "Final-test rows entered the K-Means training frame."
        )

    return training_df


def _build_native_to_canonical_mapping(
    *,
    cluster_centers: np.ndarray,
    transformed_feature_names: list[str],
) -> tuple[dict[int, int], dict[int, float]]:
    """
    Map native K-Means IDs to stable behavioral archetype IDs.

    The native cluster with the higher mean standardized activity
    score becomes canonical cluster 0 (Elevated Behavioral Activity).
    The other cluster becomes canonical cluster 1 (Routine Behavioral
    Activity).
    """

    centers = np.asarray(
        cluster_centers,
        dtype=np.float64,
    )

    if centers.shape != (
        SELECTED_K,
        len(
            EXPECTED_TRANSFORMED_FEATURE_COLUMNS
        ),
    ):
        raise ValueError(
            "Unexpected K-Means centroid matrix shape: "
            f"{centers.shape}"
        )

    score_indices = [
        transformed_feature_names.index(
            feature
        )
        for feature in ARCHETYPE_SCORE_FEATURES
    ]

    native_scores = {
        native_cluster_id: float(
            np.mean(
                centers[
                    native_cluster_id,
                    score_indices,
                ]
            )
        )
        for native_cluster_id in range(
            SELECTED_K
        )
    }

    elevated_native_cluster = max(
        native_scores,
        key=native_scores.get,
    )

    routine_native_cluster = min(
        native_scores,
        key=native_scores.get,
    )

    if (
        elevated_native_cluster
        == routine_native_cluster
    ):
        raise ValueError(
            "Could not distinguish K-Means behavioral archetypes."
        )

    elevated_score = native_scores[
        elevated_native_cluster
    ]

    routine_score = native_scores[
        routine_native_cluster
    ]

    if not (
        np.isfinite(elevated_score)
        and np.isfinite(routine_score)
    ):
        raise ValueError(
            "Behavioral archetype scores must be finite."
        )

    if not elevated_score > routine_score:
        raise ValueError(
            "Elevated archetype score must exceed "
            "routine archetype score."
        )

    mapping = {
        int(elevated_native_cluster): 0,
        int(routine_native_cluster): 1,
    }

    if set(
        mapping.keys()
    ) != {
        0,
        1,
    }:
        raise ValueError(
            "Unexpected native K-Means cluster IDs."
        )

    if set(
        mapping.values()
    ) != {
        0,
        1,
    }:
        raise ValueError(
            "Canonical K-Means cluster mapping is invalid."
        )

    return mapping, native_scores


def _canonicalize_labels(
    native_labels: np.ndarray,
    mapping: dict[int, int],
) -> np.ndarray:
    """Convert native K-Means labels into canonical archetype IDs."""

    labels = np.asarray(
        native_labels,
        dtype=np.int64,
    )

    canonical = np.array(
        [
            mapping[int(label)]
            for label in labels
        ],
        dtype=np.int64,
    )

    if set(
        np.unique(canonical)
    ) != {
        0,
        1,
    }:
        raise ValueError(
            "Final development model did not produce "
            "both canonical archetypes."
        )

    return canonical


def fit_operational_kmeans(
    *,
    dataset_path: Path = DEFAULT_DATASET_PATH,
    split_path: Path = DEFAULT_SPLIT_PATH,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Fit the final operational K-Means model on development data only.

    Fit + validation rows are used because K has already been selected.
    The final test partition remains completely excluded from model
    fitting.
    """

    training_df = build_development_training_frame(
        dataset_path=dataset_path,
        split_path=split_path,
    )

    source_features = select_kmeans_features(
        training_df
    )

    preprocessor = build_kmeans_preprocessor()

    transformed = np.asarray(
        preprocessor.fit_transform(
            source_features
        ),
        dtype=np.float64,
    )

    expected_shape = (
        FINAL_DEVELOPMENT_ROWS,
        len(
            EXPECTED_TRANSFORMED_FEATURE_COLUMNS
        ),
    )

    if transformed.shape != expected_shape:
        raise ValueError(
            "Unexpected final K-Means transformed shape: "
            f"{transformed.shape}; expected {expected_shape}."
        )

    if not np.isfinite(
        transformed
    ).all():
        raise ValueError(
            "Final K-Means transformed matrix contains "
            "non-finite values."
        )

    transformed_feature_names = (
        get_transformed_feature_names(
            preprocessor
        )
    )

    model = build_kmeans_candidate(
        SELECTED_K
    )

    native_labels = model.fit_predict(
        transformed
    )

    if model.n_clusters != SELECTED_K:
        raise ValueError(
            "Final K-Means model does not use selected K=2."
        )

    mapping, native_activity_scores = (
        _build_native_to_canonical_mapping(
            cluster_centers=model.cluster_centers_,
            transformed_feature_names=(
                transformed_feature_names
            ),
        )
    )

    canonical_labels = _canonicalize_labels(
        native_labels,
        mapping,
    )

    development_cluster_sizes = {
        str(cluster_id): int(
            np.sum(
                canonical_labels
                == cluster_id
            )
        )
        for cluster_id in [
            0,
            1,
        ]
    }

    if sum(
        development_cluster_sizes.values()
    ) != FINAL_DEVELOPMENT_ROWS:
        raise ValueError(
            "Final development cluster counts do not "
            "sum to 692."
        )

    bundle: dict[str, Any] = {
        "artifact_schema_version": 1,
        "model_name": (
            "operational_kmeans_behavioral_clustering"
        ),
        "selected_k": SELECTED_K,
        "preprocessor": preprocessor,
        "model": model,
        "source_features": list(
            MODEL_FEATURE_COLUMNS
        ),
        "transformed_features": list(
            transformed_feature_names
        ),
        "canonical_archetype_names": dict(
            CANONICAL_ARCHETYPE_NAMES
        ),
        "native_to_canonical_cluster_id": dict(
            mapping
        ),
        "archetype_score_features": list(
            ARCHETYPE_SCORE_FEATURES
        ),
    }

    metadata: dict[str, Any] = {
        "metadata_schema_version": 1,
        "model_name": (
            "operational_kmeans_behavioral_clustering"
        ),
        "model_type": "KMeans",
        "task": (
            "unsupervised_behavioral_clustering"
        ),
        "selected_k": SELECTED_K,
        "kmeans_parameters": {
            "n_clusters": SELECTED_K,
            "random_state": KMEANS_RANDOM_STATE,
            "n_init": KMEANS_N_INIT,
            "algorithm": KMEANS_ALGORITHM,
        },
        "training_partition": (
            "fit_plus_validation"
        ),
        "training_rows": FINAL_DEVELOPMENT_ROWS,
        "training_users": FINAL_DEVELOPMENT_USERS,
        "fit_rows": EXPECTED_FIT_ROWS,
        "validation_rows": (
            EXPECTED_VALIDATION_ROWS
        ),
        "test_rows_used_for_training": 0,
        "test_partition_used_for_training": False,
        "source_feature_count": len(
            MODEL_FEATURE_COLUMNS
        ),
        "transformed_feature_count": len(
            transformed_feature_names
        ),
        "source_features": list(
            MODEL_FEATURE_COLUMNS
        ),
        "transformed_features": list(
            transformed_feature_names
        ),
        "canonical_archetype_names": {
            str(cluster_id): name
            for cluster_id, name in (
                CANONICAL_ARCHETYPE_NAMES.items()
            )
        },
        "native_to_canonical_cluster_id": {
            str(native_id): int(
                canonical_id
            )
            for native_id, canonical_id in (
                mapping.items()
            )
        },
        "native_activity_scores": {
            str(native_id): float(
                score
            )
            for native_id, score in (
                native_activity_scores.items()
            )
        },
        "archetype_score_features": list(
            ARCHETYPE_SCORE_FEATURES
        ),
        "development_cluster_sizes": (
            development_cluster_sizes
        ),
        "archetype_semantics": (
            ARCHETYPE_SEMANTICS
        ),
        "risk_label_used_for_training": False,
        "scenario_type_used_for_training": False,
        "user_id_used_for_training": False,
    }

    return bundle, metadata
