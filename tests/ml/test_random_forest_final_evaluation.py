"""Tests for persisted operational Random Forest final-test results."""

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
    / "operational_random_forest_test_metrics.json"
)

SCENARIOS_PATH = (
    PROJECT_ROOT
    / "results"
    / "metrics"
    / "operational_random_forest_test_scenarios.csv"
)

PREDICTIONS_PATH = (
    PROJECT_ROOT
    / "results"
    / "predictions"
    / "operational_random_forest_test_predictions.csv"
)

EXPECTED_MODEL_FINGERPRINT = (
    "afc34ff1b02b200b6af25ac18fbda5730"
    "86c337b26b53558bf74cbc5c4cc5824"
)

EXPECTED_METADATA_FINGERPRINT = (
    "c92696b0db0b57e2a6f0ff472ca84cdb"
    "9af287290f6762803dbee3e7156647b2"
)

EXPECTED_PREDICTIONS_SHA256 = (
    "d7d9f9fb074a3675a915d896072ddbc2"
    "68ba2c5e40750c6d216cab52a0fcce67"
)

EXPECTED_SCENARIOS_SHA256 = (
    "a0608555b321f322729ddfd4a8da9f72"
    "421a77660049277611d594ce5553196f"
)

REPORT_LABEL_ORDER = [
    "low",
    "medium",
    "high",
]


def calculate_sha256(
    path: Path,
) -> str:
    """Return canonical SHA-256 for a text artifact."""

    raw_bytes = path.read_bytes()

    canonical_bytes = (
        raw_bytes
        .replace(b"\r\n", b"\n")
        .replace(b"\r", b"\n")
    )

    return hashlib.sha256(
        canonical_bytes
    ).hexdigest()


@pytest.fixture(scope="module")
def metrics() -> dict:
    """Load persisted final Random Forest metrics."""

    return json.loads(
        METRICS_PATH.read_text(
            encoding="utf-8"
        )
    )


@pytest.fixture(scope="module")
def predictions() -> pd.DataFrame:
    """Load persisted final-test predictions."""

    return pd.read_csv(
        PREDICTIONS_PATH
    )


@pytest.fixture(scope="module")
def scenarios() -> pd.DataFrame:
    """Load persisted scenario-level results."""

    return pd.read_csv(
        SCENARIOS_PATH
    )


def test_final_evaluation_files_exist() -> None:
    """All final reporting artifacts must exist."""

    assert METRICS_PATH.is_file()
    assert PREDICTIONS_PATH.is_file()
    assert SCENARIOS_PATH.is_file()

    assert METRICS_PATH.stat().st_size > 0
    assert PREDICTIONS_PATH.stat().st_size > 0
    assert SCENARIOS_PATH.stat().st_size > 0


def test_final_evaluation_identity(
    metrics: dict,
) -> None:
    """Evaluation must identify the exact frozen classifier."""

    assert metrics[
        "evaluation_schema_version"
    ] == 1

    assert metrics[
        "evaluation_status"
    ] == "final_outer_test_reporting_only"

    assert metrics[
        "model_name"
    ] == "operational_random_forest"

    assert metrics[
        "model_type"
    ] == "RandomForestClassifier"

    assert metrics[
        "selected_candidate_id"
    ] == "rf_baseline"

    assert metrics[
        "semantic_fingerprint"
    ] == EXPECTED_MODEL_FINGERPRINT

    assert metrics[
        "metadata_semantic_fingerprint"
    ] == EXPECTED_METADATA_FINGERPRINT

    assert metrics[
        "class_order"
    ] == [
        "high",
        "low",
        "medium",
    ]

    assert metrics[
        "report_label_order"
    ] == REPORT_LABEL_ORDER

    assert (
        "not evidence of real-world deployment"
        in metrics[
            "evaluation_scope"
        ]
    )

    assert (
        "must not be modified"
        in metrics[
            "model_change_prohibition"
        ]
    )


def test_final_test_partition_contract(
    metrics: dict,
    predictions: pd.DataFrame,
) -> None:
    """Persisted rows must be the frozen 153-row outer test."""

    partition = metrics[
        "test_partition"
    ]

    assert partition[
        "rows"
    ] == 153

    assert partition[
        "users"
    ] == 10

    assert partition[
        "label_distribution"
    ] == {
        "low": 98,
        "medium": 35,
        "high": 20,
    }

    assert predictions.shape == (
        153,
        13,
    )

    assert predictions.columns.tolist() == [
        "source_row_index",
        "user_id",
        "role",
        "scenario_type",
        "risk_label",
        "predicted_risk",
        "probability_low",
        "probability_medium",
        "probability_high",
        "true_class_probability",
        "predicted_confidence",
        "is_correct",
        "prediction_result",
    ]

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


def test_final_multiclass_metrics_are_frozen(
    metrics: dict,
) -> None:
    """Final held-out metrics must match the one-time evaluation."""

    final_metrics = metrics[
        "multiclass_metrics"
    ]

    expected = {
        "accuracy": 0.9803921568627451,
        "balanced_accuracy": 0.9775510204081632,
        "macro_precision": 0.9834620716973658,
        "macro_recall": 0.9775510204081632,
        "macro_f1": 0.9804311042448318,
        "weighted_f1": 0.980299837142243,
        "log_loss": 0.09978697143547707,
        "roc_auc_ovr_macro": 0.9955792794775847,
        "roc_auc_ovr_weighted": 0.9950945144364886,
    }

    for key, value in expected.items():
        assert final_metrics[
            key
        ] == pytest.approx(
            value,
            rel=0.0,
            abs=1e-15,
        )


def test_final_confusion_matrix_is_frozen(
    metrics: dict,
    predictions: pd.DataFrame,
) -> None:
    """Saved predictions must reproduce the final confusion matrix."""

    confusion = metrics[
        "confusion_matrix"
    ]

    assert confusion[
        "label_order"
    ] == REPORT_LABEL_ORDER

    assert confusion[
        "matrix"
    ] == [
        [97, 1, 0],
        [2, 33, 0],
        [0, 0, 20],
    ]

    actual_matrix = (
        pd.crosstab(
            pd.Categorical(
                predictions[
                    "risk_label"
                ],
                categories=REPORT_LABEL_ORDER,
            ),
            pd.Categorical(
                predictions[
                    "predicted_risk"
                ],
                categories=REPORT_LABEL_ORDER,
            ),
            dropna=False,
        )
        .to_numpy()
    )

    np.testing.assert_array_equal(
        actual_matrix,
        np.asarray(
            confusion[
                "matrix"
            ],
            dtype=int,
        ),
    )


def test_per_class_metrics_are_frozen(
    metrics: dict,
) -> None:
    """Per-risk-class held-out performance must remain unchanged."""

    per_class = metrics[
        "per_class_metrics"
    ]

    assert per_class[
        "low"
    ][
        "support"
    ] == 98

    assert per_class[
        "medium"
    ][
        "support"
    ] == 35

    assert per_class[
        "high"
    ][
        "support"
    ] == 20

    assert per_class[
        "low"
    ][
        "f1"
    ] == pytest.approx(
        0.9847715736040609,
        rel=0.0,
        abs=1e-15,
    )

    assert per_class[
        "medium"
    ][
        "f1"
    ] == pytest.approx(
        0.9565217391304348,
        rel=0.0,
        abs=1e-15,
    )

    assert per_class[
        "high"
    ] == {
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0,
        "support": 20,
    }


def test_error_analysis_is_frozen(
    metrics: dict,
    predictions: pd.DataFrame,
) -> None:
    """The three observed final-test errors must remain preserved."""

    error_analysis = metrics[
        "error_analysis"
    ]

    assert error_analysis[
        "correct_count"
    ] == 150

    assert error_analysis[
        "error_count"
    ] == 3

    assert error_analysis[
        "misclassification_pairs"
    ] == {
        "low_as_medium": 1,
        "medium_as_low": 2,
    }

    assert error_analysis[
        "error_scenarios"
    ] == {
        "medium_sensitive_resource_access": 1,
        "normal_office_login": 1,
        "unusual_time_login": 1,
    }

    assert int(
        predictions[
            "is_correct"
        ].sum()
    ) == 150

    errors = predictions.loc[
        ~predictions[
            "is_correct"
        ]
    ]

    assert len(
        errors
    ) == 3

    assert errors[
        "prediction_result"
    ].value_counts().to_dict() == {
        "medium_as_low": 2,
        "low_as_medium": 1,
    }


def test_probability_contract_is_preserved(
    predictions: pd.DataFrame,
) -> None:
    """Persisted class probabilities must remain valid."""

    probability_columns = [
        "probability_low",
        "probability_medium",
        "probability_high",
    ]

    probabilities = predictions[
        probability_columns
    ].to_numpy(
        dtype=np.float64
    )

    assert probabilities.shape == (
        153,
        3,
    )

    assert np.isfinite(
        probabilities
    ).all()

    assert (
        probabilities
        >=
        0.0
    ).all()

    assert (
        probabilities
        <=
        1.0
    ).all()

    np.testing.assert_allclose(
        probabilities.sum(
            axis=1
        ),
        np.ones(
            153,
            dtype=np.float64,
        ),
        rtol=0.0,
        atol=2e-15,
    )

    np.testing.assert_allclose(
        predictions[
            "predicted_confidence"
        ].to_numpy(
            dtype=np.float64
        ),
        probabilities.max(
            axis=1
        ),
        rtol=0.0,
        atol=2e-15,
    )


def test_scenario_results_match_predictions(
    predictions: pd.DataFrame,
    scenarios: pd.DataFrame,
) -> None:
    """Scenario reporting must agree with row-level predictions."""

    assert scenarios.columns.tolist() == [
        "risk_label",
        "scenario_type",
        "rows",
        "correct_predictions",
        "mean_true_class_probability",
        "mean_predicted_confidence",
        "accuracy",
    ]

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
            correct_predictions=(
                "is_correct",
                "sum",
            ),
            mean_true_class_probability=(
                "true_class_probability",
                "mean",
            ),
            mean_predicted_confidence=(
                "predicted_confidence",
                "mean",
            ),
        )
        .reset_index()
    )

    expected[
        "accuracy"
    ] = (
        expected[
            "correct_predictions"
        ]
        /
        expected[
            "rows"
        ]
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

    assert len(
        merged
    ) == len(
        scenarios
    )

    for column in [
        "rows",
        "correct_predictions",
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
        "mean_true_class_probability",
        "mean_predicted_confidence",
        "accuracy",
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


def test_result_checksums_and_provenance_are_frozen(
    metrics: dict,
) -> None:
    """Final output and training provenance checksums must remain fixed."""

    artifacts = metrics[
        "result_artifacts"
    ]

    assert artifacts[
        "predictions_sha256"
    ] == EXPECTED_PREDICTIONS_SHA256

    assert artifacts[
        "scenario_results_sha256"
    ] == EXPECTED_SCENARIOS_SHA256

    assert calculate_sha256(
        PREDICTIONS_PATH
    ) == EXPECTED_PREDICTIONS_SHA256

    assert calculate_sha256(
        SCENARIOS_PATH
    ) == EXPECTED_SCENARIOS_SHA256

    provenance = metrics[
        "training_provenance"
    ]

    assert provenance[
        "dataset_canonical_sha256"
    ] == (
        "b93e093189a130f2c7d953ff66cedd9c"
        "fcb8cfa2321b5c0c4475e68962ddff15"
    )

    assert provenance[
        "assignment_canonical_sha256"
    ] == (
        "96efcbc2b8097287b83b1ef289b46e73"
        "3bbd49bfff6d9d166a6b646c765e91ea"
    )

    assert provenance[
        "selection_canonical_sha256"
    ] == (
        "da1be58595d7605aabc66459e18fc01e"
        "346d944086a4d63219ccb7e5a660014c"
    )

    assert provenance[
        "training_metadata_final_test_accessed"
    ] is False
