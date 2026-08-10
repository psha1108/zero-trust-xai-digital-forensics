"""Persist final reporting-only evaluation of the frozen Random Forest test set."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ml.classification.data import (
    ASSIGNMENT_PATH,
    DATASET_PATH,
    EXPECTED_ASSIGNMENT_CANONICAL_SHA256,
    EXPECTED_DATASET_CANONICAL_SHA256,
    calculate_canonical_text_sha256,
)
from ml.classification.fingerprinting import (
    calculate_random_forest_metadata_semantic_fingerprint,
)
from ml.classification.inference import (
    classify_operational_records,
    load_random_forest_bundle,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SELECTION_PATH = (
    PROJECT_ROOT
    / "results"
    / "metrics"
    / "operational_random_forest_selection.json"
)

MODEL_METADATA_PATH = (
    PROJECT_ROOT
    / "model_artifacts"
    / "operational"
    / "random_forest_risk_metadata.json"
)

METRICS_PATH = (
    PROJECT_ROOT
    / "results"
    / "metrics"
    / "operational_random_forest_test_metrics.json"
)

SCENARIO_RESULTS_PATH = (
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

EXPECTED_MODEL_SEMANTIC_FINGERPRINT = (
    "afc34ff1b02b200b6af25ac18fbda5730"
    "86c337b26b53558bf74cbc5c4cc5824"
)

EXPECTED_METADATA_SEMANTIC_FINGERPRINT = (
    "c92696b0db0b57e2a6f0ff472ca84cdb"
    "9af287290f6762803dbee3e7156647b2"
)

EXPECTED_SELECTION_CANONICAL_SHA256 = (
    "da1be58595d7605aabc66459e18fc01e"
    "346d944086a4d63219ccb7e5a660014c"
)

EXPECTED_CLASS_ORDER = [
    "high",
    "low",
    "medium",
]

REPORT_LABEL_ORDER = [
    "low",
    "medium",
    "high",
]

EXPECTED_TEST_LABEL_COUNTS = {
    "low": 98,
    "medium": 35,
    "high": 20,
}


def calculate_sha256(
    path: Path,
) -> str:
    """Return a canonical cross-platform checksum for text output."""

    raw_bytes = path.read_bytes()

    canonical_bytes = (
        raw_bytes
        .replace(b"\r\n", b"\n")
        .replace(b"\r", b"\n")
    )

    return hashlib.sha256(
        canonical_bytes
    ).hexdigest()


def _refuse_existing_results() -> None:
    """Prevent accidental repeated outer-test evaluation."""

    existing_paths = [
        path
        for path in [
            METRICS_PATH,
            SCENARIO_RESULTS_PATH,
            PREDICTIONS_PATH,
        ]
        if path.exists()
    ]

    if existing_paths:
        rendered_paths = [
            str(
                path.relative_to(
                    PROJECT_ROOT
                )
            )
            for path in existing_paths
        ]

        raise FileExistsError(
            "Random Forest final-test reporting artifacts "
            "already exist; refusing to overwrite or rerun: "
            f"{rendered_paths}"
        )


def _load_and_validate_model_metadata() -> dict:
    """Load and validate frozen training-time metadata."""

    if not MODEL_METADATA_PATH.is_file():
        raise FileNotFoundError(
            "Random Forest metadata was not found: "
            f"{MODEL_METADATA_PATH}"
        )

    metadata = json.loads(
        MODEL_METADATA_PATH.read_text(
            encoding="utf-8"
        )
    )

    calculated_fingerprint = (
        calculate_random_forest_metadata_semantic_fingerprint(
            metadata
        )
    )

    if (
        calculated_fingerprint
        != EXPECTED_METADATA_SEMANTIC_FINGERPRINT
    ):
        raise ValueError(
            "Random Forest metadata semantic fingerprint "
            "does not match the frozen contract."
        )

    if (
        metadata.get(
            "metadata_semantic_fingerprint"
        )
        != EXPECTED_METADATA_SEMANTIC_FINGERPRINT
    ):
        raise ValueError(
            "Stored Random Forest metadata fingerprint "
            "does not match the frozen contract."
        )

    if (
        metadata.get(
            "semantic_fingerprint"
        )
        != EXPECTED_MODEL_SEMANTIC_FINGERPRINT
    ):
        raise ValueError(
            "Random Forest metadata references an "
            "unexpected model semantic fingerprint."
        )

    if metadata.get(
        "class_order"
    ) != EXPECTED_CLASS_ORDER:
        raise ValueError(
            "Random Forest metadata class order changed."
        )

    if metadata.get(
        "report_label_order"
    ) != REPORT_LABEL_ORDER:
        raise ValueError(
            "Random Forest report label order changed."
        )

    if metadata.get(
        "final_test_accessed"
    ) is not False:
        raise ValueError(
            "Training metadata does not confirm an untouched "
            "final test at model-freeze time."
        )

    return metadata


def main() -> None:
    """Evaluate the frozen classifier once for final reporting."""

    # ========================================================
    # 0. ONE-TIME EVALUATION GUARD
    # ========================================================

    _refuse_existing_results()

    # ========================================================
    # 1. VERIFY FROZEN PROVENANCE BEFORE TEST ACCESS
    # ========================================================

    dataset_checksum = (
        calculate_canonical_text_sha256(
            DATASET_PATH
        )
    )

    assignment_checksum = (
        calculate_canonical_text_sha256(
            ASSIGNMENT_PATH
        )
    )

    selection_checksum = (
        calculate_canonical_text_sha256(
            SELECTION_PATH
        )
    )

    if (
        dataset_checksum
        != EXPECTED_DATASET_CANONICAL_SHA256
    ):
        raise ValueError(
            "Operational dataset canonical checksum mismatch."
        )

    if (
        assignment_checksum
        != EXPECTED_ASSIGNMENT_CANONICAL_SHA256
    ):
        raise ValueError(
            "Shared split-assignment canonical checksum mismatch."
        )

    if (
        selection_checksum
        != EXPECTED_SELECTION_CANONICAL_SHA256
    ):
        raise ValueError(
            "Frozen Random Forest selection checksum mismatch."
        )

    metadata = (
        _load_and_validate_model_metadata()
    )

    bundle = load_random_forest_bundle()

    if (
        bundle[
            "semantic_fingerprint"
        ]
        != EXPECTED_MODEL_SEMANTIC_FINGERPRINT
    ):
        raise ValueError(
            "Random Forest model semantic fingerprint "
            "does not match the frozen artifact."
        )

    if bundle[
        "class_order"
    ] != EXPECTED_CLASS_ORDER:
        raise ValueError(
            "Random Forest artifact class order changed."
        )

    # ========================================================
    # 2. LOAD THE FROZEN OUTER TEST PARTITION
    # ========================================================

    dataset = pd.read_csv(
        DATASET_PATH
    )

    assignments = pd.read_csv(
        ASSIGNMENT_PATH
    )

    if len(dataset) != 845:
        raise ValueError(
            "Unexpected operational dataset row count."
        )

    if len(assignments) != 845:
        raise ValueError(
            "Unexpected split-assignment row count."
        )

    if assignments[
        "source_row_index"
    ].tolist() != list(
        range(
            len(dataset)
        )
    ):
        raise ValueError(
            "Split assignments are not aligned "
            "with source-row order."
        )

    for column in [
        "user_id",
        "role",
        "scenario_type",
        "risk_label",
    ]:
        pd.testing.assert_series_equal(
            dataset[
                column
            ].reset_index(
                drop=True
            ),
            assignments[
                column
            ].reset_index(
                drop=True
            ),
            check_names=False,
            check_dtype=False,
        )

    partition_counts = (
        assignments[
            "partition"
        ]
        .value_counts()
        .to_dict()
    )

    if partition_counts != {
        "fit": 554,
        "validation": 138,
        "test": 153,
    }:
        raise ValueError(
            "Unexpected frozen partition counts: "
            f"{partition_counts}"
        )

    working_df = dataset.copy()

    working_df[
        "source_row_index"
    ] = assignments[
        "source_row_index"
    ].to_numpy()

    working_df[
        "partition"
    ] = assignments[
        "partition"
    ].to_numpy()

    test_df = working_df.loc[
        working_df[
            "partition"
        ].eq(
            "test"
        )
    ].copy()

    development_df = working_df.loc[
        working_df[
            "partition"
        ].isin(
            [
                "fit",
                "validation",
            ]
        )
    ].copy()

    if len(test_df) != 153:
        raise ValueError(
            "Expected 153 final Random Forest test rows."
        )

    if test_df[
        "user_id"
    ].nunique() != 10:
        raise ValueError(
            "Expected 10 final Random Forest test users."
        )

    test_label_counts = {
        label: int(
            test_df[
                "risk_label"
            ].eq(
                label
            ).sum()
        )
        for label in REPORT_LABEL_ORDER
    }

    if (
        test_label_counts
        != EXPECTED_TEST_LABEL_COUNTS
    ):
        raise ValueError(
            "Unexpected final Random Forest test "
            "label distribution."
        )

    if (
        set(
            test_df[
                "user_id"
            ]
        )
        &
        set(
            development_df[
                "user_id"
            ]
        )
    ):
        raise ValueError(
            "User leakage exists between development "
            "and final Random Forest test data."
        )

    # ========================================================
    # 3. FINAL REPORTING-ONLY PREDICTION
    # ========================================================

    classified = (
        classify_operational_records(
            test_df,
            artifact_bundle=bundle,
        )
    )

    scored_test_df = pd.concat(
        [
            test_df.reset_index(
                drop=True
            ),
            classified.reset_index(
                drop=True
            ),
        ],
        axis=1,
    )

    targets = (
        scored_test_df[
            "risk_label"
        ]
        .astype(str)
        .to_numpy()
    )

    predictions = (
        scored_test_df[
            "predicted_risk"
        ]
        .astype(str)
        .to_numpy()
    )

    probability_column_by_label = {
        "low": "probability_low",
        "medium": "probability_medium",
        "high": "probability_high",
    }

    probability_columns_model_order = [
        probability_column_by_label[
            label
        ]
        for label in EXPECTED_CLASS_ORDER
    ]

    probabilities_model_order = (
        scored_test_df[
            probability_columns_model_order
        ]
        .to_numpy(
            dtype=np.float64
        )
    )

    if probabilities_model_order.shape != (
        153,
        3,
    ):
        raise RuntimeError(
            "Unexpected final Random Forest "
            "probability matrix shape."
        )

    if not np.isfinite(
        probabilities_model_order
    ).all():
        raise RuntimeError(
            "Final Random Forest probabilities "
            "contain non-finite values."
        )

    np.testing.assert_allclose(
        probabilities_model_order.sum(
            axis=1
        ),
        np.ones(
            len(test_df),
            dtype=np.float64,
        ),
        rtol=0.0,
        atol=1e-12,
    )

    # ========================================================
    # 4. MULTICLASS FINAL METRICS
    # ========================================================

    accuracy = float(
        accuracy_score(
            targets,
            predictions,
        )
    )

    balanced_accuracy = float(
        balanced_accuracy_score(
            targets,
            predictions,
        )
    )

    macro_precision = float(
        precision_score(
            targets,
            predictions,
            labels=REPORT_LABEL_ORDER,
            average="macro",
            zero_division=0,
        )
    )

    macro_recall = float(
        recall_score(
            targets,
            predictions,
            labels=REPORT_LABEL_ORDER,
            average="macro",
            zero_division=0,
        )
    )

    macro_f1 = float(
        f1_score(
            targets,
            predictions,
            labels=REPORT_LABEL_ORDER,
            average="macro",
            zero_division=0,
        )
    )

    weighted_f1 = float(
        f1_score(
            targets,
            predictions,
            labels=REPORT_LABEL_ORDER,
            average="weighted",
            zero_division=0,
        )
    )

    final_log_loss = float(
        log_loss(
            targets,
            probabilities_model_order,
            labels=EXPECTED_CLASS_ORDER,
        )
    )

    roc_auc_ovr_macro = float(
        roc_auc_score(
            targets,
            probabilities_model_order,
            labels=EXPECTED_CLASS_ORDER,
            multi_class="ovr",
            average="macro",
        )
    )

    roc_auc_ovr_weighted = float(
        roc_auc_score(
            targets,
            probabilities_model_order,
            labels=EXPECTED_CLASS_ORDER,
            multi_class="ovr",
            average="weighted",
        )
    )

    confusion = confusion_matrix(
        targets,
        predictions,
        labels=REPORT_LABEL_ORDER,
    ).astype(int)

    (
        class_precision,
        class_recall,
        class_f1,
        class_support,
    ) = precision_recall_fscore_support(
        targets,
        predictions,
        labels=REPORT_LABEL_ORDER,
        zero_division=0,
    )

    per_class_metrics = {}

    for index, label in enumerate(
        REPORT_LABEL_ORDER
    ):
        per_class_metrics[
            label
        ] = {
            "precision": float(
                class_precision[
                    index
                ]
            ),
            "recall": float(
                class_recall[
                    index
                ]
            ),
            "f1": float(
                class_f1[
                    index
                ]
            ),
            "support": int(
                class_support[
                    index
                ]
            ),
        }

    # ========================================================
    # 5. ROW-LEVEL ERROR AND CONFIDENCE ANALYSIS
    # ========================================================

    class_to_index = {
        label: index
        for index, label in enumerate(
            EXPECTED_CLASS_ORDER
        )
    }

    true_class_probabilities = np.asarray(
        [
            probabilities_model_order[
                row_index,
                class_to_index[
                    actual_label
                ],
            ]
            for row_index, actual_label in enumerate(
                targets
            )
        ],
        dtype=np.float64,
    )

    predicted_confidences = (
        probabilities_model_order.max(
            axis=1
        )
    )

    is_correct = (
        targets
        ==
        predictions
    )

    prediction_results = [
        (
            "correct"
            if actual == predicted
            else (
                f"{actual}_as_{predicted}"
            )
        )
        for actual, predicted in zip(
            targets,
            predictions,
            strict=True,
        )
    ]

    scored_test_df[
        "true_class_probability"
    ] = true_class_probabilities

    scored_test_df[
        "predicted_confidence"
    ] = predicted_confidences

    scored_test_df[
        "is_correct"
    ] = is_correct

    scored_test_df[
        "prediction_result"
    ] = prediction_results

    prediction_columns = [
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

    predictions_df = (
        scored_test_df[
            prediction_columns
        ]
        .sort_values(
            "source_row_index"
        )
        .reset_index(
            drop=True
        )
    )

    error_df = predictions_df.loc[
        ~predictions_df[
            "is_correct"
        ]
    ].copy()

    misclassification_pairs = (
        error_df[
            "prediction_result"
        ]
        .value_counts()
        .sort_index()
        .astype(int)
        .to_dict()
    )

    error_scenarios = (
        error_df[
            "scenario_type"
        ]
        .value_counts()
        .sort_index()
        .astype(int)
        .to_dict()
    )

    # ========================================================
    # 6. SCENARIO-LEVEL REPORTING
    # ========================================================

    scenario_summary = (
        scored_test_df
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

    scenario_summary[
        "accuracy"
    ] = (
        scenario_summary[
            "correct_predictions"
        ]
        /
        scenario_summary[
            "rows"
        ]
    )

    risk_order = {
        "low": 0,
        "medium": 1,
        "high": 2,
    }

    scenario_summary[
        "_risk_order"
    ] = scenario_summary[
        "risk_label"
    ].map(
        risk_order
    )

    scenario_summary = (
        scenario_summary
        .sort_values(
            [
                "_risk_order",
                "scenario_type",
            ]
        )
        .drop(
            columns=[
                "_risk_order"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # 7. SAVE DETERMINISTIC CSV REPORTING ARTIFACTS
    # ========================================================

    METRICS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    SCENARIO_RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    PREDICTIONS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    predictions_df.to_csv(
        PREDICTIONS_PATH,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
        float_format="%.15f",
    )

    scenario_summary.to_csv(
        SCENARIO_RESULTS_PATH,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
        float_format="%.12f",
    )

    # ========================================================
    # 8. SAVE FINAL METRICS REPORT
    # ========================================================

    report = {
        "evaluation_schema_version": 1,
        "evaluation_status": (
            "final_outer_test_reporting_only"
        ),
        "evaluation_scope": (
            "Synthetic operational behavioral dataset "
            "with held-out users; these metrics are "
            "not evidence of real-world deployment "
            "performance."
        ),
        "model_name": bundle[
            "model_name"
        ],
        "model_type": bundle[
            "model_type"
        ],
        "selected_candidate_id": bundle[
            "selected_candidate_id"
        ],
        "semantic_fingerprint": bundle[
            "semantic_fingerprint"
        ],
        "metadata_semantic_fingerprint": (
            metadata[
                "metadata_semantic_fingerprint"
            ]
        ),
        "class_order": list(
            EXPECTED_CLASS_ORDER
        ),
        "report_label_order": list(
            REPORT_LABEL_ORDER
        ),
        "training_provenance": {
            "dataset_canonical_sha256": (
                dataset_checksum
            ),
            "assignment_canonical_sha256": (
                assignment_checksum
            ),
            "selection_canonical_sha256": (
                selection_checksum
            ),
            "training_metadata_final_test_accessed": (
                metadata[
                    "final_test_accessed"
                ]
            ),
        },
        "test_partition": {
            "rows": int(
                len(
                    test_df
                )
            ),
            "users": int(
                test_df[
                    "user_id"
                ].nunique()
            ),
            "label_distribution": (
                test_label_counts
            ),
        },
        "multiclass_metrics": {
            "accuracy": accuracy,
            "balanced_accuracy": (
                balanced_accuracy
            ),
            "macro_precision": (
                macro_precision
            ),
            "macro_recall": (
                macro_recall
            ),
            "macro_f1": macro_f1,
            "weighted_f1": (
                weighted_f1
            ),
            "log_loss": (
                final_log_loss
            ),
            "roc_auc_ovr_macro": (
                roc_auc_ovr_macro
            ),
            "roc_auc_ovr_weighted": (
                roc_auc_ovr_weighted
            ),
        },
        "per_class_metrics": (
            per_class_metrics
        ),
        "confusion_matrix": {
            "label_order": list(
                REPORT_LABEL_ORDER
            ),
            "matrix": (
                confusion.tolist()
            ),
        },
        "error_analysis": {
            "error_count": int(
                (
                    ~is_correct
                ).sum()
            ),
            "correct_count": int(
                is_correct.sum()
            ),
            "misclassification_pairs": (
                misclassification_pairs
            ),
            "error_scenarios": (
                error_scenarios
            ),
        },
        "result_artifacts": {
            "predictions_file": str(
                PREDICTIONS_PATH.relative_to(
                    PROJECT_ROOT
                )
            ).replace(
                "\\",
                "/",
            ),
            "predictions_sha256": (
                calculate_sha256(
                    PREDICTIONS_PATH
                )
            ),
            "scenario_results_file": str(
                SCENARIO_RESULTS_PATH.relative_to(
                    PROJECT_ROOT
                )
            ).replace(
                "\\",
                "/",
            ),
            "scenario_results_sha256": (
                calculate_sha256(
                    SCENARIO_RESULTS_PATH
                )
            ),
        },
        "model_change_prohibition": (
            "The Random Forest configuration, "
            "preprocessing, features, class contract "
            "and artifact must not be modified using "
            "these outer-test results."
        ),
    }

    with METRICS_PATH.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file_handle:
        json.dump(
            report,
            file_handle,
            indent=2,
            sort_keys=True,
        )

        file_handle.write(
            "\n"
        )

    # ========================================================
    # 9. FINAL REPORTING OUTPUT
    # ========================================================

    print(
        "Final Random Forest evaluation artifacts"
    )
    print(
        "=" * 100
    )

    print(
        "Model semantic fingerprint:",
        bundle[
            "semantic_fingerprint"
        ],
    )

    print(
        "Metadata semantic fingerprint:",
        metadata[
            "metadata_semantic_fingerprint"
        ],
    )

    print(
        "Class order:",
        EXPECTED_CLASS_ORDER,
    )

    print(
        "Report label order:",
        REPORT_LABEL_ORDER,
    )

    print(
        "Test rows:",
        len(
            test_df
        ),
    )

    print(
        "Test users:",
        test_df[
            "user_id"
        ].nunique(),
    )

    print(
        "Test label distribution:",
        test_label_counts,
    )

    print(
        "\nFinal multiclass metrics"
    )

    print(
        "-" * 100
    )

    print(
        "Accuracy:",
        round(
            accuracy,
            6,
        ),
    )

    print(
        "Balanced accuracy:",
        round(
            balanced_accuracy,
            6,
        ),
    )

    print(
        "Macro precision:",
        round(
            macro_precision,
            6,
        ),
    )

    print(
        "Macro recall:",
        round(
            macro_recall,
            6,
        ),
    )

    print(
        "Macro F1:",
        round(
            macro_f1,
            6,
        ),
    )

    print(
        "Weighted F1:",
        round(
            weighted_f1,
            6,
        ),
    )

    print(
        "Log loss:",
        round(
            final_log_loss,
            6,
        ),
    )

    print(
        "ROC-AUC OVR macro:",
        round(
            roc_auc_ovr_macro,
            6,
        ),
    )

    print(
        "ROC-AUC OVR weighted:",
        round(
            roc_auc_ovr_weighted,
            6,
        ),
    )

    print(
        "\nConfusion matrix "
        "[low, medium, high]:"
    )

    print(
        confusion
    )

    print(
        "\nPer-class metrics"
    )

    print(
        "-" * 100
    )

    for label in REPORT_LABEL_ORDER:
        print(
            label,
            per_class_metrics[
                label
            ],
        )

    print(
        "\nErrors:",
        int(
            (
                ~is_correct
            ).sum()
        ),
    )

    print(
        "Misclassification pairs:",
        misclassification_pairs,
    )

    print(
        "\nSaved files"
    )

    print(
        "-" * 100
    )

    print(
        METRICS_PATH.relative_to(
            PROJECT_ROOT
        )
    )

    print(
        PREDICTIONS_PATH.relative_to(
            PROJECT_ROOT
        )
    )

    print(
        SCENARIO_RESULTS_PATH.relative_to(
            PROJECT_ROOT
        )
    )

    print(
        "\nFinal reporting artifacts saved. "
        "No model selection, retraining, "
        "feature modification or tuning was performed."
    )


if __name__ == "__main__":
    main()
