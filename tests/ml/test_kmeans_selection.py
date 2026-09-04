"""Contract tests for operational K-Means model selection."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans

from ml.clustering.preprocessing import (
    build_kmeans_preprocessor,
    select_kmeans_features,
    transform_kmeans_features,
)
from ml.clustering.selection import (
    CANDIDATE_K_VALUES,
    KMEANS_ALGORITHM,
    KMEANS_N_INIT,
    KMEANS_RANDOM_STATE,
    MIN_CLUSTER_SIZE,
    build_kmeans_candidate,
    evaluate_cluster_assignments,
    evaluate_kmeans_candidate,
    select_best_k,
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


@pytest.fixture(scope="module")
def development_matrices() -> tuple[np.ndarray, np.ndarray]:
    dataset = pd.read_csv(DATASET_PATH)
    assignments = pd.read_csv(SPLIT_PATH)

    assert len(dataset) == 845
    assert len(assignments) == 845

    working = dataset.copy()
    working["partition"] = assignments[
        "partition"
    ].to_numpy()

    fit_df = working.loc[
        working["partition"].eq("fit")
    ].copy()

    validation_df = working.loc[
        working["partition"].eq("validation")
    ].copy()

    assert len(fit_df) == 554
    assert len(validation_df) == 138

    preprocessor = build_kmeans_preprocessor()

    fit_features = select_kmeans_features(fit_df)

    fit_matrix = np.asarray(
        preprocessor.fit_transform(fit_features),
        dtype=np.float64,
    )

    validation_matrix = transform_kmeans_features(
        preprocessor,
        validation_df,
    )

    assert fit_matrix.shape == (554, 18)
    assert validation_matrix.shape == (138, 18)

    return fit_matrix, validation_matrix


def test_kmeans_selection_constants_are_frozen() -> None:
    assert CANDIDATE_K_VALUES == [
        2,
        3,
        4,
        5,
        6,
        7,
        8,
    ]

    assert KMEANS_RANDOM_STATE == 42
    assert KMEANS_N_INIT == 20
    assert KMEANS_ALGORITHM == "lloyd"
    assert MIN_CLUSTER_SIZE == 2


@pytest.mark.parametrize(
    "k",
    [2, 3, 4, 5, 6, 7, 8],
)
def test_candidate_builder_is_deterministic(
    k: int,
) -> None:
    candidate = build_kmeans_candidate(k)

    assert isinstance(candidate, KMeans)

    assert candidate.n_clusters == k
    assert candidate.random_state == 42
    assert candidate.n_init == 20
    assert candidate.algorithm == "lloyd"


def test_cluster_assignment_metrics_have_exact_contract() -> None:
    matrix = np.array(
        [
            [0.0, 0.0],
            [0.1, 0.0],
            [0.0, 0.1],
            [5.0, 5.0],
            [5.1, 5.0],
            [5.0, 5.1],
        ],
        dtype=np.float64,
    )

    labels = np.array(
        [0, 0, 0, 1, 1, 1],
        dtype=np.int64,
    )

    metrics = evaluate_cluster_assignments(
        matrix,
        labels,
        expected_k=2,
    )

    assert set(metrics) == {
        "observed_cluster_count",
        "cluster_sizes",
        "minimum_cluster_size",
        "silhouette_score",
        "davies_bouldin_index",
        "calinski_harabasz_score",
        "eligible",
    }

    assert metrics["observed_cluster_count"] == 2

    assert metrics["cluster_sizes"] == {
        "0": 3,
        "1": 3,
    }

    assert metrics["minimum_cluster_size"] == 3
    assert metrics["eligible"] is True

    assert np.isfinite(
        metrics["silhouette_score"]
    )

    assert np.isfinite(
        metrics["davies_bouldin_index"]
    )

    assert np.isfinite(
        metrics["calinski_harabasz_score"]
    )


def test_singleton_validation_cluster_is_not_eligible() -> None:
    matrix = np.array(
        [
            [0.0, 0.0],
            [0.1, 0.0],
            [0.0, 0.1],
            [5.0, 5.0],
        ],
        dtype=np.float64,
    )

    labels = np.array(
        [0, 0, 0, 1],
        dtype=np.int64,
    )

    metrics = evaluate_cluster_assignments(
        matrix,
        labels,
        expected_k=2,
    )

    assert metrics["observed_cluster_count"] == 2
    assert metrics["minimum_cluster_size"] == 1
    assert metrics["eligible"] is False


def test_real_candidate_evaluation_uses_fit_and_validation_only(
    development_matrices: tuple[np.ndarray, np.ndarray],
) -> None:
    fit_matrix, validation_matrix = (
        development_matrices
    )

    result = evaluate_kmeans_candidate(
        k=2,
        fit_matrix=fit_matrix,
        validation_matrix=validation_matrix,
    )

    assert set(result) == {
        "k",
        "parameters",
        "fit_inertia",
        "fit_metrics",
        "validation_metrics",
    }

    assert result["k"] == 2

    assert result["parameters"] == {
        "n_clusters": 2,
        "random_state": 42,
        "n_init": 20,
        "algorithm": "lloyd",
    }

    assert result["fit_inertia"] > 0

    for partition_name in [
        "fit_metrics",
        "validation_metrics",
    ]:
        metrics = result[partition_name]

        assert metrics[
            "observed_cluster_count"
        ] == 2

        assert np.isfinite(
            metrics["silhouette_score"]
        )

        assert np.isfinite(
            metrics["davies_bouldin_index"]
        )

        assert np.isfinite(
            metrics["calinski_harabasz_score"]
        )


def test_selection_prefers_highest_validation_silhouette() -> None:
    candidates = [
        {
            "k": 2,
            "validation_metrics": {
                "eligible": True,
                "silhouette_score": 0.30,
                "davies_bouldin_index": 1.10,
                "calinski_harabasz_score": 100.0,
            },
        },
        {
            "k": 3,
            "validation_metrics": {
                "eligible": True,
                "silhouette_score": 0.40,
                "davies_bouldin_index": 1.40,
                "calinski_harabasz_score": 90.0,
            },
        },
    ]

    selected = select_best_k(candidates)

    assert selected["k"] == 3


def test_selection_uses_deterministic_tie_breakers() -> None:
    candidates = [
        {
            "k": 5,
            "validation_metrics": {
                "eligible": True,
                "silhouette_score": 0.40,
                "davies_bouldin_index": 1.20,
                "calinski_harabasz_score": 110.0,
            },
        },
        {
            "k": 4,
            "validation_metrics": {
                "eligible": True,
                "silhouette_score": 0.40,
                "davies_bouldin_index": 1.10,
                "calinski_harabasz_score": 100.0,
            },
        },
        {
            "k": 3,
            "validation_metrics": {
                "eligible": True,
                "silhouette_score": 0.40,
                "davies_bouldin_index": 1.10,
                "calinski_harabasz_score": 100.0,
            },
        },
    ]

    selected = select_best_k(candidates)

    # Same silhouette:
    # lower Davies-Bouldin wins.
    # Same Davies-Bouldin and Calinski-Harabasz:
    # smaller K wins.
    assert selected["k"] == 3


def test_ineligible_candidate_cannot_be_selected() -> None:
    candidates = [
        {
            "k": 2,
            "validation_metrics": {
                "eligible": False,
                "silhouette_score": 0.99,
                "davies_bouldin_index": 0.01,
                "calinski_harabasz_score": 999.0,
            },
        },
        {
            "k": 3,
            "validation_metrics": {
                "eligible": True,
                "silhouette_score": 0.20,
                "davies_bouldin_index": 2.00,
                "calinski_harabasz_score": 50.0,
            },
        },
    ]

    selected = select_best_k(candidates)

    assert selected["k"] == 3


def test_selection_rejects_when_no_candidate_is_eligible() -> None:
    candidates = [
        {
            "k": 2,
            "validation_metrics": {
                "eligible": False,
                "silhouette_score": 0.20,
                "davies_bouldin_index": 2.0,
                "calinski_harabasz_score": 50.0,
            },
        }
    ]

    with pytest.raises(
        ValueError,
        match="No eligible",
    ):
        select_best_k(candidates)
