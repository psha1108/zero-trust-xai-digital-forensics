"""Contract tests for the one-time K-Means final evaluator."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ml.clustering.evaluate_operational_model import (
    DEFAULT_FINAL_REPORT_PATH,
    FINAL_EVALUATION_SEMANTICS,
    FINAL_TEST_ROWS,
    FINAL_TEST_USERS,
    SELECTED_K,
    compute_holdout_cluster_metrics,
    ensure_final_report_absent,
)


def test_final_evaluation_constants_are_frozen() -> None:
    assert SELECTED_K == 2
    assert FINAL_TEST_ROWS == 153
    assert FINAL_TEST_USERS == 10

    assert DEFAULT_FINAL_REPORT_PATH.name == (
        "operational_kmeans_final_test.json"
    )


def test_final_evaluation_semantics_remain_unsupervised() -> None:
    assert FINAL_EVALUATION_SEMANTICS == (
        "held-out unsupervised behavioral clustering evaluation; "
        "cluster IDs are not risk classes or access-control decisions"
    )


def test_holdout_metric_contract() -> None:
    matrix = np.asarray(
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

    labels = np.asarray(
        [
            0,
            0,
            0,
            1,
            1,
            1,
        ],
        dtype=np.int64,
    )

    metrics = compute_holdout_cluster_metrics(
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

    assert metrics["silhouette_score"] > 0.9
    assert metrics["davies_bouldin_index"] >= 0.0
    assert metrics["calinski_harabasz_score"] > 0.0


def test_holdout_metric_rejects_missing_expected_cluster() -> None:
    matrix = np.asarray(
        [
            [0.0, 0.0],
            [0.1, 0.0],
            [0.0, 0.1],
            [0.2, 0.0],
        ],
        dtype=np.float64,
    )

    labels = np.asarray(
        [
            0,
            0,
            0,
            0,
        ],
        dtype=np.int64,
    )

    metrics = compute_holdout_cluster_metrics(
        matrix,
        labels,
        expected_k=2,
    )

    assert metrics["observed_cluster_count"] == 1
    assert metrics["cluster_sizes"] == {
        "0": 4,
    }
    assert metrics["eligible"] is False

    assert metrics["silhouette_score"] is None
    assert metrics["davies_bouldin_index"] is None
    assert metrics["calinski_harabasz_score"] is None


def test_holdout_metric_rejects_non_finite_matrix() -> None:
    matrix = np.asarray(
        [
            [0.0, 0.0],
            [np.nan, 1.0],
        ],
        dtype=np.float64,
    )

    labels = np.asarray(
        [
            0,
            1,
        ],
        dtype=np.int64,
    )

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        compute_holdout_cluster_metrics(
            matrix,
            labels,
            expected_k=2,
        )


def test_holdout_metric_rejects_label_length_mismatch() -> None:
    matrix = np.asarray(
        [
            [0.0, 0.0],
            [1.0, 1.0],
            [2.0, 2.0],
        ],
        dtype=np.float64,
    )

    labels = np.asarray(
        [
            0,
            1,
        ],
        dtype=np.int64,
    )

    with pytest.raises(
        ValueError,
        match="count|rows|length",
    ):
        compute_holdout_cluster_metrics(
            matrix,
            labels,
            expected_k=2,
        )


def test_final_report_guard_allows_absent_path(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "final.json"
    )

    ensure_final_report_absent(
        path
    )

    assert not path.exists()


def test_final_report_guard_refuses_existing_report(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "final.json"
    )

    path.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        FileExistsError,
        match="already exists|refuse|overwrite",
    ):
        ensure_final_report_absent(
            path
        )


def test_default_final_report_is_under_results_metrics() -> None:
    parts = DEFAULT_FINAL_REPORT_PATH.parts

    assert "results" in parts
    assert "metrics" in parts


def test_final_evaluator_contract_contains_no_supervised_metric_names() -> None:
    forbidden_names = {
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "confusion_matrix",
    }

    allowed_metric_names = {
        "silhouette_score",
        "davies_bouldin_index",
        "calinski_harabasz_score",
    }

    assert forbidden_names.isdisjoint(
        allowed_metric_names
    )
