"""Development-only behavioral archetype profiling for K-Means."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.clustering.persist_operational_model import (
    DEFAULT_ARTIFACT_PATH,
    load_operational_kmeans_bundle,
)
from ml.clustering.preprocessing import (
    EXPECTED_TRANSFORMED_FEATURE_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    NUMERIC_FEATURE_COLUMNS,
    ROLE_CATEGORIES,
    select_kmeans_features,
)
from ml.clustering.train_operational_model import (
    ARCHETYPE_SCORE_FEATURES,
    CANONICAL_ARCHETYPE_NAMES,
    SELECTED_K,
)


PROFILE_SEMANTICS = (
    "behavioral context only; cluster IDs are not risk "
    "classes or access-control decisions"
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "ml_training_dataset.csv"
)

SPLIT_ASSIGNMENTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "operational"
    / "isolation_forest_split_assignments.csv"
)

EXPECTED_TOTAL_ROWS = 845
EXPECTED_DEVELOPMENT_ROWS = 692
EXPECTED_DEVELOPMENT_USERS = 40

EXPECTED_PARTITION_ROWS = {
    "fit": 554,
    "validation": 138,
}


def _load_development_frame() -> tuple[
    pd.DataFrame,
    dict[str, int],
]:
    """
    Load only the fit + validation rows used for descriptive profiling.

    The split file contains the held-out test assignments for audit
    purposes, but test rows are not selected, transformed, predicted,
    or included in any profile calculation.
    """

    dataset = pd.read_csv(
        DATASET_PATH
    )

    assignments = pd.read_csv(
        SPLIT_ASSIGNMENTS_PATH
    )

    if len(dataset) != EXPECTED_TOTAL_ROWS:
        raise ValueError(
            "Unexpected operational dataset row count: "
            f"{len(dataset)}."
        )

    if len(assignments) != EXPECTED_TOTAL_ROWS:
        raise ValueError(
            "Unexpected split-assignment row count: "
            f"{len(assignments)}."
        )

    required_assignment_columns = {
        "source_row_index",
        "user_id",
        "partition",
    }

    missing_assignment_columns = (
        required_assignment_columns
        - set(assignments.columns)
    )

    if missing_assignment_columns:
        raise ValueError(
            "Split assignments are missing required columns: "
            + ", ".join(
                sorted(
                    missing_assignment_columns
                )
            )
        )

    source_indices = pd.to_numeric(
        assignments[
            "source_row_index"
        ],
        errors="raise",
    ).astype(
        np.int64
    )

    if source_indices.duplicated().any():
        raise ValueError(
            "Split assignments contain duplicate source_row_index "
            "values."
        )

    if set(
        source_indices.tolist()
    ) != set(
        range(
            EXPECTED_TOTAL_ROWS
        )
    ):
        raise ValueError(
            "Split assignments do not cover the exact source rows."
        )

    aligned_dataset = (
        dataset.iloc[
            source_indices.to_numpy()
        ]
        .reset_index(
            drop=True
        )
    )

    aligned_assignments = (
        assignments.reset_index(
            drop=True
        )
    )

    dataset_users = (
        aligned_dataset[
            "user_id"
        ]
        .astype(str)
        .to_numpy()
    )

    assignment_users = (
        aligned_assignments[
            "user_id"
        ]
        .astype(str)
        .to_numpy()
    )

    if not np.array_equal(
        dataset_users,
        assignment_users,
    ):
        raise ValueError(
            "Operational dataset and split assignments "
            "are not aligned by user_id."
        )

    development_mask = (
        aligned_assignments[
            "partition"
        ].isin(
            [
                "fit",
                "validation",
            ]
        )
    )

    development = (
        aligned_dataset.loc[
            development_mask
        ]
        .reset_index(
            drop=True
        )
    )

    development_partitions = (
        aligned_assignments.loc[
            development_mask,
            "partition",
        ]
        .reset_index(
            drop=True
        )
    )

    if len(
        development
    ) != EXPECTED_DEVELOPMENT_ROWS:
        raise ValueError(
            "Unexpected development row count: "
            f"{len(development)}."
        )

    user_count = int(
        development[
            "user_id"
        ].nunique()
    )

    if user_count != EXPECTED_DEVELOPMENT_USERS:
        raise ValueError(
            "Unexpected development user count: "
            f"{user_count}."
        )

    partition_rows = {
        partition: int(
            (
                development_partitions
                == partition
            ).sum()
        )
        for partition in (
            "fit",
            "validation",
        )
    }

    if (
        partition_rows
        != EXPECTED_PARTITION_ROWS
    ):
        raise ValueError(
            "Unexpected development partition counts: "
            f"{partition_rows}."
        )

    return (
        development,
        partition_rows,
    )


def _validate_frozen_bundle(
    bundle: dict[str, Any],
) -> None:
    """Validate the behavioral contract of the frozen artifact."""

    if int(
        bundle.get(
            "selected_k",
            -1,
        )
    ) != SELECTED_K:
        raise ValueError(
            "Frozen K-Means artifact does not use selected K=2."
        )

    if list(
        bundle.get(
            "source_features",
            [],
        )
    ) != list(
        MODEL_FEATURE_COLUMNS
    ):
        raise ValueError(
            "Frozen K-Means source-feature contract changed."
        )

    if list(
        bundle.get(
            "transformed_features",
            [],
        )
    ) != list(
        EXPECTED_TRANSFORMED_FEATURE_COLUMNS
    ):
        raise ValueError(
            "Frozen K-Means transformed-feature contract changed."
        )

    names = bundle.get(
        "canonical_archetype_names"
    )

    if names != CANONICAL_ARCHETYPE_NAMES:
        raise ValueError(
            "Frozen K-Means archetype-name contract changed."
        )

    mapping = {
        int(
            native_id
        ): int(
            canonical_id
        )
        for native_id, canonical_id in (
            bundle.get(
                "native_to_canonical_cluster_id",
                {},
            ).items()
        )
    }

    if set(
        mapping.keys()
    ) != {
        0,
        1,
    }:
        raise ValueError(
            "Frozen native K-Means cluster mapping is invalid."
        )

    if set(
        mapping.values()
    ) != {
        0,
        1,
    }:
        raise ValueError(
            "Frozen canonical K-Means cluster mapping is invalid."
        )


def _canonical_activity_scores(
    bundle: dict[str, Any],
) -> dict[int, float]:
    """
    Return canonical standardized activity scores from frozen centroids.

    These scores use only the seven behavioral activity features that
    were frozen when assigning canonical semantic cluster IDs.
    """

    transformed_names = list(
        EXPECTED_TRANSFORMED_FEATURE_COLUMNS
    )

    feature_indices = [
        transformed_names.index(
            feature
        )
        for feature in (
            ARCHETYPE_SCORE_FEATURES
        )
    ]

    centers = np.asarray(
        bundle[
            "model"
        ].cluster_centers_,
        dtype=np.float64,
    )

    mapping = {
        int(
            native_id
        ): int(
            canonical_id
        )
        for native_id, canonical_id in (
            bundle[
                "native_to_canonical_cluster_id"
            ].items()
        )
    }

    scores: dict[
        int,
        float,
    ] = {}

    for native_id, canonical_id in (
        mapping.items()
    ):
        score = float(
            np.mean(
                centers[
                    native_id,
                    feature_indices,
                ]
            )
        )

        if not np.isfinite(
            score
        ):
            raise ValueError(
                "Frozen K-Means centroid produced a "
                "non-finite activity score."
            )

        scores[
            canonical_id
        ] = score

    if set(
        scores
    ) != {
        0,
        1,
    }:
        raise ValueError(
            "Canonical activity scores are incomplete."
        )

    return scores


def build_development_archetype_profile_report() -> dict[
    str,
    Any,
]:
    """
    Build descriptive K-Means profiles from development data only.

    The held-out test partition is not transformed or predicted here.
    Risk labels and scenario types remain audit columns only and are
    not passed into the K-Means feature pipeline.
    """

    development, partition_rows = (
        _load_development_frame()
    )

    bundle = load_operational_kmeans_bundle(
        DEFAULT_ARTIFACT_PATH
    )

    _validate_frozen_bundle(
        bundle
    )

    feature_frame = (
        select_kmeans_features(
            development
        )
        .reset_index(
            drop=True
        )
    )

    transformed = np.asarray(
        bundle[
            "preprocessor"
        ].transform(
            feature_frame
        ),
        dtype=np.float64,
    )

    expected_shape = (
        EXPECTED_DEVELOPMENT_ROWS,
        len(
            EXPECTED_TRANSFORMED_FEATURE_COLUMNS
        ),
    )

    if transformed.shape != expected_shape:
        raise ValueError(
            "Unexpected development transformed shape: "
            f"{transformed.shape}; expected {expected_shape}."
        )

    if not np.isfinite(
        transformed
    ).all():
        raise ValueError(
            "Development transformed matrix contains "
            "non-finite values."
        )

    native_labels = np.asarray(
        bundle[
            "model"
        ].predict(
            transformed
        ),
        dtype=np.int64,
    )

    if native_labels.shape != (
        EXPECTED_DEVELOPMENT_ROWS,
    ):
        raise ValueError(
            "Development prediction count is invalid."
        )

    mapping = {
        int(
            native_id
        ): int(
            canonical_id
        )
        for native_id, canonical_id in (
            bundle[
                "native_to_canonical_cluster_id"
            ].items()
        )
    }

    canonical_labels = np.asarray(
        [
            mapping[
                int(
                    native_label
                )
            ]
            for native_label in (
                native_labels
            )
        ],
        dtype=np.int64,
    )

    canonical_names = {
        str(
            cluster_id
        ): str(
            name
        )
        for cluster_id, name in (
            bundle[
                "canonical_archetype_names"
            ].items()
        )
    }

    activity_scores = (
        _canonical_activity_scores(
            bundle
        )
    )

    development_cluster_sizes = {
        str(
            cluster_id
        ): int(
            (
                canonical_labels
                == cluster_id
            ).sum()
        )
        for cluster_id in (
            0,
            1,
        )
    }

    if sum(
        development_cluster_sizes.values()
    ) != EXPECTED_DEVELOPMENT_ROWS:
        raise ValueError(
            "Development cluster sizes do not sum to 692."
        )

    profiles: dict[
        str,
        dict[str, Any],
    ] = {}

    for cluster_id in (
        0,
        1,
    ):
        cluster_key = str(
            cluster_id
        )

        row_mask = (
            canonical_labels
            == cluster_id
        )

        row_count = int(
            row_mask.sum()
        )

        if row_count <= 0:
            raise ValueError(
                f"Canonical cluster {cluster_id} is empty."
            )

        cluster_features = (
            feature_frame.loc[
                row_mask
            ]
        )

        role_distribution = {
            role: float(
                (
                    cluster_features[
                        "role"
                    ]
                    == role
                ).sum()
                / row_count
            )
            for role in (
                ROLE_CATEGORIES
            )
        }

        numeric_feature_means = {
            feature: float(
                pd.to_numeric(
                    cluster_features[
                        feature
                    ],
                    errors="raise",
                ).mean()
            )
            for feature in (
                NUMERIC_FEATURE_COLUMNS
            )
        }

        profiles[
            cluster_key
        ] = {
            "cluster_id": (
                cluster_id
            ),
            "archetype_name": (
                canonical_names[
                    cluster_key
                ]
            ),
            "row_count": (
                row_count
            ),
            "row_fraction": float(
                row_count
                / EXPECTED_DEVELOPMENT_ROWS
            ),
            "role_distribution": (
                role_distribution
            ),
            "numeric_feature_means": (
                numeric_feature_means
            ),
            "standardized_activity_score": float(
                activity_scores[
                    cluster_id
                ]
            ),
        }

    return {
        "task": (
            "development_behavioral_archetype_profiling"
        ),
        "profile_partition": (
            "fit_plus_validation"
        ),
        "development_rows": (
            EXPECTED_DEVELOPMENT_ROWS
        ),
        "development_users": (
            EXPECTED_DEVELOPMENT_USERS
        ),
        "partition_rows": (
            partition_rows
        ),
        "selected_k": (
            SELECTED_K
        ),
        "source_features": list(
            MODEL_FEATURE_COLUMNS
        ),
        "canonical_archetype_names": (
            canonical_names
        ),
        "development_cluster_sizes": (
            development_cluster_sizes
        ),
        "profiles": (
            profiles
        ),
        "semantics": (
            PROFILE_SEMANTICS
        ),
        "risk_label_used_for_profile": (
            False
        ),
        "scenario_type_used_for_profile": (
            False
        ),
        "test_partition_used_for_profile": (
            False
        ),
        "test_rows_evaluated": (
            0
        ),
        "policy_decision_produced": (
            False
        ),
    }
