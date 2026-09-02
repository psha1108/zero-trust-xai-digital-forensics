"""One-time held-out evaluation for frozen operational K-Means."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

from ml.clustering.persist_operational_model import (
    DEFAULT_ARTIFACT_PATH,
    load_operational_kmeans_bundle,
)
from ml.clustering.preprocessing import (
    EXPECTED_TRANSFORMED_FEATURE_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    select_kmeans_features,
)
from ml.clustering.train_operational_model import (
    CANONICAL_ARCHETYPE_NAMES,
    SELECTED_K as TRAINED_SELECTED_K,
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

DEFAULT_FINAL_REPORT_PATH = (
    PROJECT_ROOT
    / "results"
    / "metrics"
    / "operational_kmeans_final_test.json"
)

SELECTED_K = int(
    TRAINED_SELECTED_K
)

FINAL_TEST_ROWS = 153
FINAL_TEST_USERS = 10
EXPECTED_TOTAL_ROWS = 845

FROZEN_ARTIFACT_SHA256 = (
    "39c8647ea8b317c765ec3e8decac9794"
    "ea4b71c3377452d33091ce4b237a7f7d"
)

FROZEN_MODEL_FINGERPRINT_SHA256 = (
    "9059ca795d0317fafd420761d7a226fe"
    "de6d9bdaf7b600d92df626dd09b34392"
)

FINAL_EVALUATION_SEMANTICS = (
    "held-out unsupervised behavioral clustering evaluation; "
    "cluster IDs are not risk classes or access-control decisions"
)


def _sha256_file(
    path: Path,
) -> str:
    """Return the byte-exact SHA-256 digest for one file."""

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:
        for chunk in iter(
            lambda: handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def ensure_final_report_absent(
    path: Path,
) -> None:
    """Refuse to overwrite an existing official final report."""

    output_path = Path(
        path
    )

    if output_path.exists():
        raise FileExistsError(
            "Official final K-Means report already exists; "
            "refuse to overwrite it."
        )


def _validate_metric_matrix(
    matrix: np.ndarray,
) -> np.ndarray:
    """Validate the transformed matrix used for clustering metrics."""

    values = np.asarray(
        matrix,
        dtype=np.float64,
    )

    if values.ndim != 2:
        raise ValueError(
            "Holdout metric matrix must be two-dimensional."
        )

    if values.shape[0] < 2:
        raise ValueError(
            "Holdout metric matrix must contain at least two rows."
        )

    if values.shape[1] < 1:
        raise ValueError(
            "Holdout metric matrix must contain at least one feature."
        )

    if not np.isfinite(
        values
    ).all():
        raise ValueError(
            "Holdout metric matrix must contain only finite values."
        )

    return values


def _validate_metric_labels(
    labels: np.ndarray,
    *,
    expected_rows: int,
) -> np.ndarray:
    """Validate one-dimensional integer cluster assignments."""

    raw = np.asarray(
        labels
    )

    if raw.ndim != 1:
        raise ValueError(
            "Holdout cluster labels must be one-dimensional."
        )

    if len(raw) != expected_rows:
        raise ValueError(
            "Holdout cluster label count must match matrix rows."
        )

    try:
        numeric = raw.astype(
            np.float64
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "Holdout cluster labels must be numeric integers."
        ) from exc

    if not np.isfinite(
        numeric
    ).all():
        raise ValueError(
            "Holdout cluster labels must be finite."
        )

    if not np.equal(
        numeric,
        np.floor(
            numeric
        ),
    ).all():
        raise ValueError(
            "Holdout cluster labels must be integers."
        )

    return numeric.astype(
        np.int64
    )


def compute_holdout_cluster_metrics(
    matrix: np.ndarray,
    labels: np.ndarray,
    *,
    expected_k: int,
) -> dict[str, Any]:
    """Compute unsupervised clustering metrics for fixed assignments."""

    values = _validate_metric_matrix(
        matrix
    )

    cluster_labels = _validate_metric_labels(
        labels,
        expected_rows=values.shape[0],
    )

    if (
        not isinstance(
            expected_k,
            int,
        )
        or isinstance(
            expected_k,
            bool,
        )
        or expected_k < 2
    ):
        raise ValueError(
            "expected_k must be an integer greater than or equal to 2."
        )

    unique_labels, counts = np.unique(
        cluster_labels,
        return_counts=True,
    )

    cluster_sizes = {
        str(
            int(
                cluster_id
            )
        ): int(
            count
        )
        for cluster_id, count in zip(
            unique_labels,
            counts,
            strict=True,
        )
    }

    observed_cluster_count = int(
        len(
            unique_labels
        )
    )

    minimum_cluster_size = (
        int(
            counts.min()
        )
        if len(
            counts
        )
        else 0
    )

    eligible = bool(
        observed_cluster_count
        == expected_k
        and minimum_cluster_size
        >= 2
    )

    silhouette: float | None = None
    davies_bouldin: float | None = None
    calinski_harabasz: float | None = None

    if eligible:
        silhouette = float(
            silhouette_score(
                values,
                cluster_labels,
            )
        )

        davies_bouldin = float(
            davies_bouldin_score(
                values,
                cluster_labels,
            )
        )

        calinski_harabasz = float(
            calinski_harabasz_score(
                values,
                cluster_labels,
            )
        )

        calculated = (
            silhouette,
            davies_bouldin,
            calinski_harabasz,
        )

        if not all(
            np.isfinite(
                value
            )
            for value in calculated
        ):
            raise ValueError(
                "Holdout clustering metrics must be finite."
            )

    return {
        "observed_cluster_count": (
            observed_cluster_count
        ),
        "cluster_sizes": (
            cluster_sizes
        ),
        "minimum_cluster_size": (
            minimum_cluster_size
        ),
        "silhouette_score": (
            silhouette
        ),
        "davies_bouldin_index": (
            davies_bouldin
        ),
        "calinski_harabasz_score": (
            calinski_harabasz
        ),
        "eligible": (
            eligible
        ),
    }


def _load_final_test_frame() -> pd.DataFrame:
    """
    Load the authoritative held-out partition.

    This function is intentionally called only by the explicit final
    evaluation path, never during module import or unit testing.
    """

    dataset = pd.read_csv(
        DATASET_PATH
    )

    assignments = pd.read_csv(
        SPLIT_ASSIGNMENTS_PATH
    )

    if len(
        dataset
    ) != EXPECTED_TOTAL_ROWS:
        raise ValueError(
            "Unexpected operational dataset row count."
        )

    if len(
        assignments
    ) != EXPECTED_TOTAL_ROWS:
        raise ValueError(
            "Unexpected split-assignment row count."
        )

    required_columns = {
        "source_row_index",
        "user_id",
        "partition",
    }

    missing = (
        required_columns
        - set(
            assignments.columns
        )
    )

    if missing:
        raise ValueError(
            "Split assignments are missing required columns: "
            + ", ".join(
                sorted(
                    missing
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
            "Split assignments contain duplicate source rows."
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
            "Dataset and split assignments are not aligned by user."
        )

    test_mask = (
        aligned_assignments[
            "partition"
        ]
        == "test"
    )

    final_test = (
        aligned_dataset.loc[
            test_mask
        ]
        .reset_index(
            drop=True
        )
    )

    if len(
        final_test
    ) != FINAL_TEST_ROWS:
        raise ValueError(
            "Unexpected final-test row count."
        )

    final_test_users = int(
        final_test[
            "user_id"
        ].nunique()
    )

    if final_test_users != FINAL_TEST_USERS:
        raise ValueError(
            "Unexpected final-test user count."
        )

    return final_test


def _validate_frozen_bundle(
    bundle: dict[str, Any],
) -> None:
    """Validate the frozen artifact contract before final evaluation."""

    if int(
        bundle.get(
            "selected_k",
            -1,
        )
    ) != SELECTED_K:
        raise ValueError(
            "Frozen K-Means artifact selected_k changed."
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

    if (
        bundle.get(
            "canonical_archetype_names"
        )
        != CANONICAL_ARCHETYPE_NAMES
    ):
        raise ValueError(
            "Frozen K-Means archetype-name contract changed."
        )

    model_fingerprint = bundle.get(
        "model_fingerprint_sha256"
    )

    if (
        model_fingerprint
        != FROZEN_MODEL_FINGERPRINT_SHA256
    ):
        raise ValueError(
            "Frozen K-Means semantic model fingerprint changed."
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
            "Frozen native cluster mapping changed."
        )

    if set(
        mapping.values()
    ) != {
        0,
        1,
    }:
        raise ValueError(
            "Frozen canonical cluster mapping changed."
        )


def build_final_holdout_report() -> dict[str, Any]:
    """
    Evaluate the frozen K-Means artifact on the held-out partition.

    Calling this function constitutes final-test evaluation. It is not
    called during normal unit tests.
    """

    artifact_hash = _sha256_file(
        DEFAULT_ARTIFACT_PATH
    )

    if (
        artifact_hash
        != FROZEN_ARTIFACT_SHA256
    ):
        raise ValueError(
            "Frozen K-Means artifact SHA-256 changed."
        )

    final_test = (
        _load_final_test_frame()
    )

    bundle = load_operational_kmeans_bundle(
        DEFAULT_ARTIFACT_PATH
    )

    _validate_frozen_bundle(
        bundle
    )

    feature_frame = (
        select_kmeans_features(
            final_test
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
        FINAL_TEST_ROWS,
        len(
            EXPECTED_TRANSFORMED_FEATURE_COLUMNS
        ),
    )

    if transformed.shape != expected_shape:
        raise ValueError(
            "Unexpected final-test transformed shape."
        )

    if not np.isfinite(
        transformed
    ).all():
        raise ValueError(
            "Final-test transformed matrix contains non-finite values."
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
        FINAL_TEST_ROWS,
    ):
        raise ValueError(
            "Unexpected final-test prediction count."
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

    metrics = (
        compute_holdout_cluster_metrics(
            transformed,
            canonical_labels,
            expected_k=SELECTED_K,
        )
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

    return {
        "task": (
            "final_held_out_behavioral_clustering_evaluation"
        ),
        "evaluation_partition": (
            "test"
        ),
        "final_test_rows": (
            FINAL_TEST_ROWS
        ),
        "final_test_users": (
            FINAL_TEST_USERS
        ),
        "selected_k": (
            SELECTED_K
        ),
        "source_features": list(
            MODEL_FEATURE_COLUMNS
        ),
        "transformed_feature_count": len(
            EXPECTED_TRANSFORMED_FEATURE_COLUMNS
        ),
        "canonical_archetype_names": (
            canonical_names
        ),
        "metrics": (
            metrics
        ),
        "semantics": (
            FINAL_EVALUATION_SEMANTICS
        ),
        "artifact_sha256": (
            artifact_hash
        ),
        "model_fingerprint_sha256": (
            bundle[
                "model_fingerprint_sha256"
            ]
        ),
        "risk_label_used_for_evaluation": (
            False
        ),
        "scenario_type_used_for_evaluation": (
            False
        ),
        "supervised_metrics_computed": (
            False
        ),
        "policy_decision_produced": (
            False
        ),
    }


def write_final_holdout_report_once(
    path: Path = DEFAULT_FINAL_REPORT_PATH,
) -> dict[str, Any]:
    """
    Perform final evaluation and create the official report exactly once.

    An existing output path is never overwritten.
    """

    output_path = Path(
        path
    )

    ensure_final_report_absent(
        output_path
    )

    report = (
        build_final_holdout_report()
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    serialized = json.dumps(
        report,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )

    try:
        with output_path.open(
            "x",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(
                serialized
            )
            handle.write(
                "\n"
            )
    except FileExistsError as exc:
        raise FileExistsError(
            "Official final K-Means report already exists; "
            "refuse to overwrite it."
        ) from exc

    return report


def main() -> None:
    """Execute the explicit one-time final K-Means evaluation."""

    report = (
        write_final_holdout_report_once()
    )

    metrics = report[
        "metrics"
    ]

    print(
        "Operational K-Means final held-out evaluation complete."
    )
    print(
        "Final-test rows:",
        report[
            "final_test_rows"
        ],
    )
    print(
        "Final-test users:",
        report[
            "final_test_users"
        ],
    )
    print(
        "Canonical cluster sizes:",
        metrics[
            "cluster_sizes"
        ],
    )
    print(
        "Silhouette score:",
        metrics[
            "silhouette_score"
        ],
    )
    print(
        "Davies-Bouldin index:",
        metrics[
            "davies_bouldin_index"
        ],
    )
    print(
        "Calinski-Harabasz score:",
        metrics[
            "calinski_harabasz_score"
        ],
    )
    print(
        "Official report:",
        DEFAULT_FINAL_REPORT_PATH,
    )


if __name__ == "__main__":
    main()
