"""Tests for persisted operational Random Forest model selection."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from ml.classification.data import (
    EXPECTED_ASSIGNMENT_CANONICAL_SHA256,
    EXPECTED_DATASET_CANONICAL_SHA256,
)
from ml.classification.selection_protocol import (
    CANDIDATE_CONFIGURATIONS,
    get_candidate_parameters,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CANDIDATE_RESULTS_PATH = (
    PROJECT_ROOT
    / "results"
    / "metrics"
    / "operational_random_forest_validation_candidates.csv"
)

SELECTION_METADATA_PATH = (
    PROJECT_ROOT
    / "results"
    / "metrics"
    / "operational_random_forest_selection.json"
)


@pytest.fixture(scope="module")
def candidate_results() -> pd.DataFrame:
    """Load persisted candidate-comparison results."""

    return pd.read_csv(
        CANDIDATE_RESULTS_PATH
    )


@pytest.fixture(scope="module")
def selection_metadata() -> dict:
    """Load persisted Random Forest selection metadata."""

    with SELECTION_METADATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as file_handle:
        return json.load(file_handle)


def test_selection_artifacts_exist() -> None:
    """Both persisted validation-selection artifacts must exist."""

    assert CANDIDATE_RESULTS_PATH.is_file()
    assert SELECTION_METADATA_PATH.is_file()

    assert CANDIDATE_RESULTS_PATH.stat().st_size > 0
    assert SELECTION_METADATA_PATH.stat().st_size > 0


def test_candidate_set_matches_frozen_protocol(
    candidate_results: pd.DataFrame,
) -> None:
    """Persisted candidates must exactly match the predeclared set."""

    expected_ids = [
        candidate["candidate_id"]
        for candidate in CANDIDATE_CONFIGURATIONS
    ]

    assert len(candidate_results) == 8

    assert set(
        candidate_results["candidate_id"]
    ) == set(expected_ids)

    assert candidate_results[
        "candidate_id"
    ].is_unique

    assert sorted(
        candidate_results["rank"].tolist()
    ) == list(range(1, 9))


def test_selected_candidate_is_frozen_baseline(
    candidate_results: pd.DataFrame,
    selection_metadata: dict,
) -> None:
    """The frozen validation winner must remain rf_baseline."""

    selected_row = candidate_results.loc[
        candidate_results["rank"].eq(1)
    ].iloc[0]

    assert selected_row[
        "candidate_id"
    ] == "rf_baseline"

    assert selection_metadata[
        "selected_candidate_id"
    ] == "rf_baseline"

    baseline_candidate = next(
        candidate
        for candidate in CANDIDATE_CONFIGURATIONS
        if candidate["candidate_id"] == "rf_baseline"
    )

    assert selection_metadata[
        "selected_parameters"
    ] == get_candidate_parameters(
        baseline_candidate
    )


def test_selected_validation_metrics_are_preserved(
    candidate_results: pd.DataFrame,
    selection_metadata: dict,
) -> None:
    """The observed frozen validation metrics must reproduce."""

    selected_row = candidate_results.loc[
        candidate_results["rank"].eq(1)
    ].iloc[0]

    assert selected_row[
        "macro_f1"
    ] == pytest.approx(
        0.9765631163992756,
        rel=0.0,
        abs=1e-12,
    )

    assert selected_row[
        "balanced_accuracy"
    ] == pytest.approx(
        0.9676767676767677,
        rel=0.0,
        abs=1e-12,
    )

    assert selected_row[
        "log_loss"
    ] == pytest.approx(
        0.089565,
        rel=0.0,
        abs=1e-6,
    )

    assert selected_row[
        "accuracy"
    ] == pytest.approx(
        136 / 138,
        rel=0.0,
        abs=1e-12,
    )

    assert int(
        selected_row[
            "validation_errors"
        ]
    ) == 2

    metadata_metrics = selection_metadata[
        "selected_validation_metrics"
    ]

    assert metadata_metrics[
        "macro_f1"
    ] == pytest.approx(
        selected_row["macro_f1"],
        rel=0.0,
        abs=1e-15,
    )

    assert metadata_metrics[
        "balanced_accuracy"
    ] == pytest.approx(
        selected_row["balanced_accuracy"],
        rel=0.0,
        abs=1e-15,
    )


def test_all_candidates_had_same_classification_metrics(
    candidate_results: pd.DataFrame,
) -> None:
    """Only probability quality separated the frozen candidates."""

    assert candidate_results[
        "macro_f1"
    ].nunique() == 1

    assert candidate_results[
        "balanced_accuracy"
    ].nunique() == 1

    assert candidate_results[
        "accuracy"
    ].nunique() == 1

    assert candidate_results[
        "validation_errors"
    ].nunique() == 1

    assert candidate_results[
        "validation_errors"
    ].iloc[0] == 2

    baseline_loss = float(
        candidate_results.loc[
            candidate_results[
                "candidate_id"
            ].eq("rf_baseline"),
            "log_loss",
        ].iloc[0]
    )

    assert baseline_loss == pytest.approx(
        candidate_results[
            "log_loss"
        ].min(),
        rel=0.0,
        abs=1e-15,
    )


def test_selection_partition_and_fingerprint_contract(
    selection_metadata: dict,
) -> None:
    """Selection metadata must identify approved development data."""

    assert selection_metadata[
        "selection_schema_version"
    ] == 1

    assert selection_metadata[
        "selection_status"
    ] == "validation_selection_frozen"

    assert selection_metadata[
        "final_test_accessed"
    ] is False

    assert selection_metadata[
        "fit_rows"
    ] == 554

    assert selection_metadata[
        "fit_users"
    ] == 32

    assert selection_metadata[
        "validation_rows"
    ] == 138

    assert selection_metadata[
        "validation_users"
    ] == 8

    assert selection_metadata[
        "dataset_canonical_sha256"
    ] == EXPECTED_DATASET_CANONICAL_SHA256

    assert selection_metadata[
        "split_assignment_canonical_sha256"
    ] == EXPECTED_ASSIGNMENT_CANONICAL_SHA256


def test_class_order_and_reporting_order_are_explicit(
    selection_metadata: dict,
) -> None:
    """Probability order must come from the fitted classifier."""

    assert selection_metadata[
        "model_class_order"
    ] == [
        "high",
        "low",
        "medium",
    ]

    assert selection_metadata[
        "report_label_order"
    ] == [
        "low",
        "medium",
        "high",
    ]

    assert (
        selection_metadata[
            "model_class_order"
        ]
        !=
        selection_metadata[
            "report_label_order"
        ]
    )


def test_selection_rationale_records_log_loss_tiebreak(
    selection_metadata: dict,
) -> None:
    """Metadata must explain why baseline won the classification tie."""

    rationale = selection_metadata[
        "selection_rationale"
    ]

    assert "identical" in rationale
    assert "log loss" in rationale
    assert "rf_baseline" in rationale
