"""Tests for persisted operational Isolation Forest test results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]

METRICS_PATH = (
    PROJECT_ROOT
    / "results"
    / "metrics"
    / "operational_isolation_forest_test_metrics.json"
)

SCENARIOS_PATH = (
    PROJECT_ROOT
    / "results"
    / "metrics"
    / "operational_isolation_forest_test_scenarios.csv"
)

PREDICTIONS_PATH = (
    PROJECT_ROOT
    / "results"
    / "predictions"
    / "operational_isolation_forest_test_predictions.csv"
)

EXPECTED_FINGERPRINT = (
    "77b1dc298717107f1b1bd353d6da4a01c"
    "6fd2f00bf348a3cb4026cde0897d44e"
)

EXPECTED_THRESHOLD = 0.5532259181941123


def calculate_sha256(path: Path) -> str:
    """Return a file SHA-256 checksum."""

    digest = hashlib.sha256()

    with path.open("rb") as file_handle:
        for block in iter(
            lambda: file_handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


@pytest.fixture(scope="module")
def metrics() -> dict:
    """Load the persisted final metrics."""

    with METRICS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file_handle:
        return json.load(file_handle)


@pytest.fixture(scope="module")
def predictions() -> pd.DataFrame:
    """Load persisted outer-test predictions."""

    return pd.read_csv(PREDICTIONS_PATH)


@pytest.fixture(scope="module")
def scenarios() -> pd.DataFrame:
    """Load persisted scenario-level results."""

    return pd.read_csv(SCENARIOS_PATH)


def test_final_evaluation_files_exist() -> None:
    """All final reporting artifacts must exist."""

    assert METRICS_PATH.is_file()
    assert PREDICTIONS_PATH.is_file()
    assert SCENARIOS_PATH.is_file()

    assert METRICS_PATH.stat().st_size > 0
    assert PREDICTIONS_PATH.stat().st_size > 0
    assert SCENARIOS_PATH.stat().st_size > 0


def test_evaluation_identity_and_status(
    metrics: dict,
) -> None:
    """Evaluation must identify the frozen final model."""

    assert metrics[
        "evaluation_schema_version"
    ] == 1

    assert metrics[
        "evaluation_status"
    ] == "final_outer_test_reporting_only"

    assert metrics[
        "model_name"
    ] == "operational_isolation_forest"

    assert metrics[
        "semantic_fingerprint"
    ] == EXPECTED_FINGERPRINT

    assert metrics[
        "frozen_anomaly_threshold"
    ] == pytest.approx(
        EXPECTED_THRESHOLD,
        rel=0.0,
        abs=1e-15,
    )

    assert "must not be modified" in metrics[
        "model_change_prohibition"
    ]


def test_final_test_partition_contract(
    metrics: dict,
    predictions: pd.DataFrame,
) -> None:
    """Persisted predictions must represent the frozen test set."""

    partition = metrics["test_partition"]

    assert partition["rows"] == 153
    assert partition["users"] == 10

    assert partition[
        "label_distribution"
    ] == {
        "low": 98,
        "medium": 35,
        "high": 20,
    }

    assert predictions.shape == (
        153,
        12,
    )

    assert predictions[
        "source_row_index"
    ].is_unique

    assert predictions[
        "source_row_index"
    ].is_monotonic_increasing

    assert predictions[
        "user_id"
    ].nunique() == 10

    assert predictions[
        "risk_label"
    ].value_counts().to_dict() == {
        "low": 98,
        "medium": 35,
        "high": 20,
    }


def test_final_metrics_are_frozen(
    metrics: dict,
) -> None:
    """Final test metrics must match the reported evaluation."""

    ranking = metrics[
        "threshold_independent_metrics"
    ]

    thresholded = metrics[
        "frozen_threshold_metrics"
    ]

    assert ranking[
        "roc_auc"
    ] == pytest.approx(
        0.9434137291280148,
        rel=0.0,
        abs=1e-15,
    )

    assert ranking[
        "average_precision"
    ] == pytest.approx(
        0.9260409896059065,
        rel=0.0,
        abs=1e-15,
    )

    assert thresholded[
        "true_negative"
    ] == 85

    assert thresholded[
        "false_positive"
    ] == 13

    assert thresholded[
        "false_negative"
    ] == 4

    assert thresholded[
        "true_positive"
    ] == 51

    assert thresholded[
        "precision"
    ] == pytest.approx(
        51 / 64,
        rel=0.0,
        abs=1e-15,
    )

    assert thresholded[
        "recall"
    ] == pytest.approx(
        51 / 55,
        rel=0.0,
        abs=1e-15,
    )

    assert thresholded[
        "f1"
    ] == pytest.approx(
        0.8571428571428571,
        rel=0.0,
        abs=1e-15,
    )

    assert thresholded[
        "balanced_accuracy"
    ] == pytest.approx(
        0.8973098330241187,
        rel=0.0,
        abs=1e-15,
    )


def test_prediction_counts_match_confusion_matrix(
    metrics: dict,
    predictions: pd.DataFrame,
) -> None:
    """Prediction rows must reproduce the saved confusion matrix."""

    result_counts = predictions[
        "prediction_result"
    ].value_counts().to_dict()

    assert result_counts == {
        "correct": 136,
        "false_positive": 13,
        "false_negative": 4,
    }

    predicted_anomalies = int(
        predictions[
            "binary_prediction"
        ].sum()
    )

    actual_anomalies = int(
        predictions[
            "binary_target"
        ].sum()
    )

    assert predicted_anomalies == 64
    assert actual_anomalies == 55

    assert np.allclose(
        predictions[
            "threshold_margin"
        ].to_numpy(),
        (
            predictions[
                "anomaly_score"
            ].to_numpy()
            -
            predictions[
                "anomaly_threshold"
            ].to_numpy()
        ),
        rtol=0.0,
        atol=2e-15,
    )

    assert (
        predictions[
            "anomaly_threshold"
        ].nunique()
        ==
        1
    )

    assert predictions[
        "anomaly_threshold"
    ].iloc[0] == pytest.approx(
        EXPECTED_THRESHOLD,
        rel=0.0,
        abs=1e-15,
    )


def test_risk_detection_rates(
    metrics: dict,
) -> None:
    """Risk-level detection rates must remain unchanged."""

    risk_metrics = metrics[
        "risk_label_metrics"
    ]

    assert risk_metrics["low"][
        "predicted_anomalies"
    ] == 13

    assert risk_metrics["medium"][
        "predicted_anomalies"
    ] == 31

    assert risk_metrics["high"][
        "predicted_anomalies"
    ] == 20

    assert risk_metrics["medium"][
        "detection_rate"
    ] == pytest.approx(
        31 / 35,
        rel=0.0,
        abs=1e-15,
    )

    assert risk_metrics["high"][
        "detection_rate"
    ] == pytest.approx(
        1.0,
        rel=0.0,
        abs=0.0,
    )


def test_error_analysis_is_preserved(
    metrics: dict,
) -> None:
    """Persisted error analysis must match final observations."""

    error_analysis = metrics[
        "error_analysis"
    ]

    assert error_analysis[
        "false_positive_count"
    ] == 13

    assert error_analysis[
        "false_negative_count"
    ] == 4

    assert error_analysis[
        "false_negative_scenarios"
    ] == {
        "slightly_high_failed_attempts": 1,
        "unusual_time_login": 3,
    }

    assert error_analysis[
        "false_positive_scenarios"
    ] == {
        "normal_admin_login": 7,
        "normal_office_login": 4,
        "normal_resource_access": 2,
    }


def test_scenario_results_match_predictions(
    predictions: pd.DataFrame,
    scenarios: pd.DataFrame,
) -> None:
    """Scenario aggregates must agree with row-level predictions."""

    assert len(scenarios) == 16

    expected = (
        predictions
        .groupby(
            [
                "risk_label",
                "scenario_type",
            ],
            observed=True,
        )
        .agg(
            rows=(
                "scenario_type",
                "size",
            ),
            predicted_anomalies=(
                "is_anomaly",
                "sum",
            ),
            mean_score=(
                "anomaly_score",
                "mean",
            ),
            minimum_score=(
                "anomaly_score",
                "min",
            ),
            maximum_score=(
                "anomaly_score",
                "max",
            ),
        )
        .reset_index()
    )

    expected[
        "detection_rate"
    ] = (
        expected[
            "predicted_anomalies"
        ]
        /
        expected["rows"]
    )

    merged = scenarios.merge(
        expected,
        on=[
            "risk_label",
            "scenario_type",
        ],
        suffixes=(
            "_saved",
            "_expected",
        ),
        validate="one_to_one",
    )

    assert len(merged) == 16

    for column in [
        "rows",
        "predicted_anomalies",
    ]:
        np.testing.assert_array_equal(
            merged[
                f"{column}_saved"
            ].to_numpy(),
            merged[
                f"{column}_expected"
            ].to_numpy(),
        )

    for column in [
        "mean_score",
        "minimum_score",
        "maximum_score",
        "detection_rate",
    ]:
        np.testing.assert_allclose(
            merged[
                f"{column}_saved"
            ].to_numpy(),
            merged[
                f"{column}_expected"
            ].to_numpy(),
            rtol=0.0,
            atol=1e-12,
        )


def test_result_checksums_match_metrics(
    metrics: dict,
) -> None:
    """Metrics must identify the persisted CSV artifacts."""

    artifacts = metrics[
        "result_artifacts"
    ]

    assert artifacts[
        "predictions_sha256"
    ] == calculate_sha256(
        PREDICTIONS_PATH
    )

    assert artifacts[
        "scenario_results_sha256"
    ] == calculate_sha256(
        SCENARIOS_PATH
    )
