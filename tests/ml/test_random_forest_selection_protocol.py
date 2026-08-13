"""Tests for the frozen Random Forest selection protocol."""

from __future__ import annotations

from ml.classification.selection_protocol import (
    CANDIDATE_CONFIGURATIONS,
    N_ESTIMATORS,
    N_JOBS,
    PRIMARY_SELECTION_METRIC,
    RANDOM_STATE,
    SECONDARY_SELECTION_METRIC,
    TERTIARY_SELECTION_METRIC,
    get_candidate_parameters,
)


def test_selection_metrics_are_frozen() -> None:
    """Model-selection priorities must remain explicit."""

    assert PRIMARY_SELECTION_METRIC == "macro_f1"
    assert SECONDARY_SELECTION_METRIC == "balanced_accuracy"
    assert TERTIARY_SELECTION_METRIC == "log_loss"


def test_candidate_set_is_small_and_unique() -> None:
    """Candidate search must remain bounded and reproducible."""

    assert len(CANDIDATE_CONFIGURATIONS) == 8

    candidate_ids = [
        candidate["candidate_id"]
        for candidate in CANDIDATE_CONFIGURATIONS
    ]

    assert len(candidate_ids) == len(
        set(candidate_ids)
    )

    assert candidate_ids[0] == "rf_baseline"


def test_all_candidates_use_frozen_common_parameters() -> None:
    """Every candidate must share the fixed reproducibility settings."""

    for candidate in CANDIDATE_CONFIGURATIONS:
        parameters = get_candidate_parameters(
            candidate
        )

        assert parameters["n_estimators"] == (
            N_ESTIMATORS
        )

        assert parameters["random_state"] == (
            RANDOM_STATE
        )

        assert parameters["n_jobs"] == N_JOBS

        assert parameters["n_estimators"] == 300
        assert parameters["random_state"] == 42
        assert parameters["n_jobs"] == 1


def test_no_unapproved_candidate_dimensions() -> None:
    """The frozen comparison must not silently expand its search."""

    allowed_criteria = {
        "gini",
        "entropy",
    }

    allowed_depths = {
        None,
        12,
    }

    allowed_leaf_sizes = {
        1,
        2,
    }

    allowed_class_weights = {
        None,
        "balanced",
    }

    for candidate in CANDIDATE_CONFIGURATIONS:
        assert candidate[
            "criterion"
        ] in allowed_criteria

        assert candidate[
            "max_depth"
        ] in allowed_depths

        assert candidate[
            "min_samples_leaf"
        ] in allowed_leaf_sizes

        assert candidate[
            "class_weight"
        ] in allowed_class_weights

        assert candidate[
            "max_features"
        ] == "sqrt"

        assert candidate[
            "min_samples_split"
        ] == 2

        assert candidate[
            "bootstrap"
        ] is True
