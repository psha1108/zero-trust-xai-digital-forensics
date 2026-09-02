"""Tests for reproducible operational K-Means selection reporting."""

from pathlib import Path

import numpy as np

from ml.clustering.select_operational_model import (
    build_selection_report,
    run_development_selection,
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


def test_development_selection_uses_only_fit_and_validation() -> None:
    result = run_development_selection(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    assert result["fit_rows"] == 554
    assert result["validation_rows"] == 138

    assert result["fit_users"] == 32
    assert result["validation_users"] == 8

    assert result["user_overlap"] == 0

    assert result["test_rows_evaluated"] == 0

    assert result["candidate_k_values"] == [
        2,
        3,
        4,
        5,
        6,
        7,
        8,
    ]

    assert result["selected_k"] == 2


def test_selected_k_matches_frozen_development_metrics() -> None:
    result = run_development_selection(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    selected = result["selected_candidate"]

    validation = selected[
        "validation_metrics"
    ]

    assert selected["k"] == 2

    assert validation["eligible"] is True

    assert validation[
        "observed_cluster_count"
    ] == 2

    assert validation["cluster_sizes"] == {
        "0": 15,
        "1": 123,
    }

    assert np.isclose(
        validation["silhouette_score"],
        0.461901472363,
        rtol=0.0,
        atol=1e-10,
    )

    assert np.isclose(
        validation["davies_bouldin_index"],
        1.468248642801,
        rtol=0.0,
        atol=1e-10,
    )

    assert np.isclose(
        validation["calinski_harabasz_score"],
        36.741960715914,
        rtol=0.0,
        atol=1e-10,
    )


def test_selection_report_records_unsupervised_contract() -> None:
    development = run_development_selection(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    report = build_selection_report(
        development
    )

    assert report[
        "model_name"
    ] == "operational_kmeans_behavioral_clustering"

    assert report[
        "model_type"
    ] == "KMeans"

    assert report[
        "task"
    ] == "unsupervised_behavioral_clustering"

    assert report[
        "selected_k"
    ] == 2

    assert report[
        "selection_metric"
    ] == "validation_silhouette_score"

    assert report[
        "risk_label_used_for_training"
    ] is False

    assert report[
        "risk_label_used_for_selection"
    ] is False

    assert report[
        "scenario_type_used_for_training"
    ] is False

    assert report[
        "test_partition_used_for_selection"
    ] is False

    assert report[
        "test_rows_evaluated"
    ] == 0


def test_selection_report_has_behavioral_archetype_names() -> None:
    development = run_development_selection(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    report = build_selection_report(
        development
    )

    assert report[
        "development_archetypes"
    ] == {
        "0": "Elevated Behavioral Activity",
        "1": "Routine Behavioral Activity",
    }

    assert report[
        "archetype_semantics"
    ] == (
        "behavioral context only; cluster IDs are not "
        "risk classes or access-control decisions"
    )


def test_selection_runner_is_deterministic() -> None:
    first = run_development_selection(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    second = run_development_selection(
        dataset_path=DATASET_PATH,
        split_path=SPLIT_PATH,
    )

    assert first["selected_k"] == second["selected_k"]

    first_candidates = first["candidates"]
    second_candidates = second["candidates"]

    assert len(first_candidates) == 7
    assert len(second_candidates) == 7

    for left, right in zip(
        first_candidates,
        second_candidates,
    ):
        assert left["k"] == right["k"]

        assert np.isclose(
            left["fit_inertia"],
            right["fit_inertia"],
            rtol=0.0,
            atol=1e-8,
        )

        for partition in [
            "fit_metrics",
            "validation_metrics",
        ]:
            left_metrics = left[partition]
            right_metrics = right[partition]

            assert (
                left_metrics["cluster_sizes"]
                == right_metrics["cluster_sizes"]
            )

            assert (
                left_metrics["eligible"]
                == right_metrics["eligible"]
            )

            for metric in [
                "silhouette_score",
                "davies_bouldin_index",
                "calinski_harabasz_score",
            ]:
                assert np.isclose(
                    left_metrics[metric],
                    right_metrics[metric],
                    rtol=0.0,
                    atol=1e-8,
                )
