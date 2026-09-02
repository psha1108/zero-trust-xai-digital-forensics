"""Deterministic candidate evaluation for operational K-Means."""

from __future__ import annotations

from collections import Counter
from typing import Final, Sequence

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)


CANDIDATE_K_VALUES: Final[list[int]] = [
    2,
    3,
    4,
    5,
    6,
    7,
    8,
]

KMEANS_RANDOM_STATE: Final[int] = 42
KMEANS_N_INIT: Final[int] = 20
KMEANS_ALGORITHM: Final[str] = "lloyd"

# Validation clusters smaller than this are not eligible
# for model selection.
MIN_CLUSTER_SIZE: Final[int] = 2


def _validate_matrix(
    matrix: np.ndarray,
    *,
    name: str,
) -> np.ndarray:
    """Validate one transformed K-Means feature matrix."""

    array = np.asarray(
        matrix,
        dtype=np.float64,
    )

    if array.ndim != 2:
        raise ValueError(
            f"{name} must be a two-dimensional matrix."
        )

    if array.shape[0] < 2:
        raise ValueError(
            f"{name} must contain at least two rows."
        )

    if array.shape[1] < 1:
        raise ValueError(
            f"{name} must contain at least one feature."
        )

    if not np.isfinite(array).all():
        raise ValueError(
            f"{name} contains non-finite values."
        )

    return array


def build_kmeans_candidate(
    k: int,
) -> KMeans:
    """Build one deterministic K-Means candidate."""

    if not isinstance(k, int):
        raise TypeError(
            "k must be an integer."
        )

    if k < 2:
        raise ValueError(
            "k must be at least 2."
        )

    return KMeans(
        n_clusters=k,
        random_state=KMEANS_RANDOM_STATE,
        n_init=KMEANS_N_INIT,
        algorithm=KMEANS_ALGORITHM,
    )


def evaluate_cluster_assignments(
    matrix: np.ndarray,
    labels: np.ndarray,
    *,
    expected_k: int,
) -> dict[str, object]:
    """
    Evaluate one set of cluster assignments.

    Eligibility requires:
    - exactly the requested number of observed clusters; and
    - at least MIN_CLUSTER_SIZE members in every cluster.

    Metrics are still calculated when mathematically valid, even when
    a candidate is ineligible because one cluster is too small.
    """

    matrix_array = _validate_matrix(
        matrix,
        name="matrix",
    )

    label_array = np.asarray(labels)

    if label_array.ndim != 1:
        raise ValueError(
            "labels must be one-dimensional."
        )

    if len(label_array) != len(matrix_array):
        raise ValueError(
            "labels length must match matrix row count."
        )

    if not isinstance(expected_k, int):
        raise TypeError(
            "expected_k must be an integer."
        )

    if expected_k < 2:
        raise ValueError(
            "expected_k must be at least 2."
        )

    unique_labels = np.unique(label_array)
    observed_cluster_count = int(
        len(unique_labels)
    )

    cluster_counts = Counter(
        int(label)
        for label in label_array
    )

    cluster_sizes = {
        str(cluster_id): int(cluster_counts[cluster_id])
        for cluster_id in sorted(cluster_counts)
    }

    minimum_cluster_size = (
        min(cluster_sizes.values())
        if cluster_sizes
        else 0
    )

    metric_valid = (
        observed_cluster_count >= 2
        and observed_cluster_count < len(matrix_array)
    )

    if metric_valid:
        silhouette = float(
            silhouette_score(
                matrix_array,
                label_array,
            )
        )

        davies_bouldin = float(
            davies_bouldin_score(
                matrix_array,
                label_array,
            )
        )

        calinski_harabasz = float(
            calinski_harabasz_score(
                matrix_array,
                label_array,
            )
        )
    else:
        silhouette = float("nan")
        davies_bouldin = float("nan")
        calinski_harabasz = float("nan")

    eligible = bool(
        observed_cluster_count == expected_k
        and minimum_cluster_size >= MIN_CLUSTER_SIZE
        and metric_valid
        and np.isfinite(silhouette)
        and np.isfinite(davies_bouldin)
        and np.isfinite(calinski_harabasz)
    )

    return {
        "observed_cluster_count": observed_cluster_count,
        "cluster_sizes": cluster_sizes,
        "minimum_cluster_size": int(
            minimum_cluster_size
        ),
        "silhouette_score": silhouette,
        "davies_bouldin_index": davies_bouldin,
        "calinski_harabasz_score": calinski_harabasz,
        "eligible": eligible,
    }


def evaluate_kmeans_candidate(
    *,
    k: int,
    fit_matrix: np.ndarray,
    validation_matrix: np.ndarray,
) -> dict[str, object]:
    """
    Fit one K-Means candidate on fit data and evaluate fit/validation.

    The final held-out test partition must never be supplied here.
    """

    fit_array = _validate_matrix(
        fit_matrix,
        name="fit_matrix",
    )

    validation_array = _validate_matrix(
        validation_matrix,
        name="validation_matrix",
    )

    if fit_array.shape[1] != validation_array.shape[1]:
        raise ValueError(
            "Fit and validation matrices must have the same "
            "feature dimension."
        )

    if k >= len(fit_array):
        raise ValueError(
            "k must be smaller than the number of fit rows."
        )

    candidate = build_kmeans_candidate(k)

    fit_labels = candidate.fit_predict(
        fit_array
    )

    validation_labels = candidate.predict(
        validation_array
    )

    fit_metrics = evaluate_cluster_assignments(
        fit_array,
        fit_labels,
        expected_k=k,
    )

    validation_metrics = evaluate_cluster_assignments(
        validation_array,
        validation_labels,
        expected_k=k,
    )

    return {
        "k": int(k),
        "parameters": {
            "n_clusters": int(k),
            "random_state": KMEANS_RANDOM_STATE,
            "n_init": KMEANS_N_INIT,
            "algorithm": KMEANS_ALGORITHM,
        },
        "fit_inertia": float(
            candidate.inertia_
        ),
        "fit_metrics": fit_metrics,
        "validation_metrics": validation_metrics,
    }


def select_best_k(
    candidates: Sequence[dict[str, object]],
) -> dict[str, object]:
    """
    Select the best eligible candidate using the frozen ranking rule.

    Ranking:
    1. higher validation silhouette;
    2. lower validation Davies-Bouldin;
    3. higher validation Calinski-Harabasz;
    4. smaller K.
    """

    if not candidates:
        raise ValueError(
            "No K-Means candidates were provided."
        )

    eligible_candidates = []

    for candidate in candidates:
        if "k" not in candidate:
            raise ValueError(
                "Candidate is missing k."
            )

        validation_metrics = candidate.get(
            "validation_metrics"
        )

        if not isinstance(
            validation_metrics,
            dict,
        ):
            raise ValueError(
                "Candidate is missing validation_metrics."
            )

        if bool(
            validation_metrics.get(
                "eligible",
                False,
            )
        ):
            eligible_candidates.append(
                candidate
            )

    if not eligible_candidates:
        raise ValueError(
            "No eligible K-Means candidates were found."
        )

    def ranking_key(
        candidate: dict[str, object],
    ) -> tuple[float, float, float, int]:
        metrics = candidate[
            "validation_metrics"
        ]

        assert isinstance(metrics, dict)

        silhouette = float(
            metrics["silhouette_score"]
        )

        davies_bouldin = float(
            metrics["davies_bouldin_index"]
        )

        calinski_harabasz = float(
            metrics["calinski_harabasz_score"]
        )

        k = int(candidate["k"])

        if not all(
            np.isfinite(value)
            for value in [
                silhouette,
                davies_bouldin,
                calinski_harabasz,
            ]
        ):
            raise ValueError(
                f"Eligible candidate K={k} contains "
                "non-finite validation metrics."
            )

        return (
            silhouette,
            -davies_bouldin,
            calinski_harabasz,
            -k,
        )

    return max(
        eligible_candidates,
        key=ranking_key,
    )
