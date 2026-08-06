"""Persist final reporting-only evaluation of the frozen outer test set."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ml.anomaly_detection.inference import (
    load_isolation_forest_bundle,
    score_operational_records,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "ml_training_dataset.csv"
)

ASSIGNMENT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "operational"
    / "isolation_forest_split_assignments.csv"
)

METRICS_PATH = (
    PROJECT_ROOT
    / "results"
    / "metrics"
    / "operational_isolation_forest_test_metrics.json"
)

SCENARIO_RESULTS_PATH = (
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


def calculate_sha256(path: Path) -> str:
    """Return the SHA-256 checksum of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as file_handle:
        for block in iter(
            lambda: file_handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def main() -> None:
    """Evaluate and persist the frozen outer-test results."""

    dataset = pd.read_csv(DATASET_PATH)
    assignments = pd.read_csv(ASSIGNMENT_PATH)

    assert len(dataset) == 845
    assert len(assignments) == 845

    assert assignments[
        "source_row_index"
    ].tolist() == list(range(len(dataset)))

    for column in [
        "user_id",
        "role",
        "scenario_type",
        "risk_label",
    ]:
        pd.testing.assert_series_equal(
            dataset[column].reset_index(drop=True),
            assignments[column].reset_index(drop=True),
            check_names=False,
            check_dtype=False,
        )

    working_df = dataset.copy()

    working_df["source_row_index"] = assignments[
        "source_row_index"
    ].to_numpy()

    working_df["partition"] = assignments[
        "partition"
    ].to_numpy()

    test_df = working_df.loc[
        working_df["partition"].eq("test")
    ].copy()

    assert len(test_df) == 153
    assert test_df["user_id"].nunique() == 10

    assert (
        test_df["risk_label"]
        .value_counts()
        .to_dict()
        ==
        {
            "low": 98,
            "medium": 35,
            "high": 20,
        }
    )

    bundle = load_isolation_forest_bundle()

    scored_results = score_operational_records(
        test_df,
        artifact_bundle=bundle,
    )

    scored_test_df = pd.concat(
        [
            test_df.reset_index(drop=True),
            scored_results.reset_index(drop=True),
        ],
        axis=1,
    )

    binary_labels = (
        scored_test_df["risk_label"]
        .ne("low")
        .astype("uint8")
        .to_numpy()
    )

    predictions = (
        scored_test_df["is_anomaly"]
        .astype("uint8")
        .to_numpy()
    )

    scores = scored_test_df[
        "anomaly_score"
    ].to_numpy()

    tn, fp, fn, tp = confusion_matrix(
        binary_labels,
        predictions,
        labels=[0, 1],
    ).ravel()

    roc_auc = float(
        roc_auc_score(
            binary_labels,
            scores,
        )
    )

    average_precision = float(
        average_precision_score(
            binary_labels,
            scores,
        )
    )

    precision = float(
        precision_score(
            binary_labels,
            predictions,
            zero_division=0,
        )
    )

    recall = float(
        recall_score(
            binary_labels,
            predictions,
            zero_division=0,
        )
    )

    f1 = float(
        f1_score(
            binary_labels,
            predictions,
            zero_division=0,
        )
    )

    balanced_accuracy = float(
        balanced_accuracy_score(
            binary_labels,
            predictions,
        )
    )

    specificity = float(
        tn / (tn + fp)
    )

    false_positive_rate = float(
        fp / (tn + fp)
    )

    assert (
        int(tn),
        int(fp),
        int(fn),
        int(tp),
    ) == (
        85,
        13,
        4,
        51,
    )

    scored_test_df[
        "binary_target"
    ] = binary_labels

    scored_test_df[
        "binary_prediction"
    ] = predictions

    scored_test_df[
        "prediction_result"
    ] = np.select(
        [
            (
                scored_test_df[
                    "binary_target"
                ].eq(0)
                &
                scored_test_df[
                    "binary_prediction"
                ].eq(1)
            ),
            (
                scored_test_df[
                    "binary_target"
                ].eq(1)
                &
                scored_test_df[
                    "binary_prediction"
                ].eq(0)
            ),
        ],
        [
            "false_positive",
            "false_negative",
        ],
        default="correct",
    )

    prediction_columns = [
        "source_row_index",
        "user_id",
        "role",
        "scenario_type",
        "risk_label",
        "binary_target",
        "anomaly_score",
        "anomaly_threshold",
        "threshold_margin",
        "is_anomaly",
        "binary_prediction",
        "prediction_result",
    ]

    predictions_df = (
        scored_test_df[
            prediction_columns
        ]
        .sort_values(
            "source_row_index"
        )
        .reset_index(drop=True)
    )

    risk_summary = (
        scored_test_df
        .groupby(
            "risk_label",
            observed=True,
        )
        .agg(
            rows=(
                "risk_label",
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
            median_score=(
                "anomaly_score",
                "median",
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
        .reindex(
            [
                "low",
                "medium",
                "high",
            ]
        )
    )

    risk_summary[
        "detection_rate"
    ] = (
        risk_summary[
            "predicted_anomalies"
        ]
        /
        risk_summary["rows"]
    )

    assert risk_summary[
        "predicted_anomalies"
    ].astype(int).to_dict() == {
        "low": 13,
        "medium": 31,
        "high": 20,
    }

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

    scenario_summary[
        "detection_rate"
    ] = (
        scenario_summary[
            "predicted_anomalies"
        ]
        /
        scenario_summary["rows"]
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
    ].map(risk_order)

    scenario_summary = (
        scenario_summary
        .sort_values(
            [
                "_risk_order",
                "scenario_type",
            ]
        )
        .drop(
            columns="_risk_order"
        )
        .reset_index(drop=True)
    )

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

    risk_metrics = {}

    for risk_label, row in (
        risk_summary.iterrows()
    ):
        risk_metrics[risk_label] = {
            "rows": int(row["rows"]),
            "predicted_anomalies": int(
                row[
                    "predicted_anomalies"
                ]
            ),
            "detection_rate": float(
                row["detection_rate"]
            ),
            "mean_score": float(
                row["mean_score"]
            ),
            "median_score": float(
                row["median_score"]
            ),
            "minimum_score": float(
                row["minimum_score"]
            ),
            "maximum_score": float(
                row["maximum_score"]
            ),
        }

    false_negative_scenarios = (
        predictions_df.loc[
            predictions_df[
                "prediction_result"
            ].eq("false_negative"),
            "scenario_type",
        ]
        .value_counts()
        .sort_index()
        .astype(int)
        .to_dict()
    )

    false_positive_scenarios = (
        predictions_df.loc[
            predictions_df[
                "prediction_result"
            ].eq("false_positive"),
            "scenario_type",
        ]
        .value_counts()
        .sort_index()
        .astype(int)
        .to_dict()
    )

    report = {
        "evaluation_schema_version": 1,
        "evaluation_status": (
            "final_outer_test_reporting_only"
        ),
        "model_name": bundle[
            "model_name"
        ],
        "semantic_fingerprint": bundle[
            "semantic_fingerprint"
        ],
        "frozen_anomaly_threshold": float(
            bundle[
                "anomaly_threshold"
            ]
        ),
        "test_partition": {
            "rows": len(test_df),
            "users": int(
                test_df[
                    "user_id"
                ].nunique()
            ),
            "label_distribution": {
                "low": 98,
                "medium": 35,
                "high": 20,
            },
            "binary_anomaly_prevalence": float(
                binary_labels.mean()
            ),
        },
        "threshold_independent_metrics": {
            "roc_auc": roc_auc,
            "average_precision": (
                average_precision
            ),
            "random_ranking_ap_baseline": float(
                binary_labels.mean()
            ),
        },
        "frozen_threshold_metrics": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "balanced_accuracy": (
                balanced_accuracy
            ),
            "specificity": specificity,
            "false_positive_rate": (
                false_positive_rate
            ),
        },
        "risk_label_metrics": risk_metrics,
        "error_analysis": {
            "false_positive_count": int(fp),
            "false_negative_count": int(fn),
            "false_positive_scenarios": (
                false_positive_scenarios
            ),
            "false_negative_scenarios": (
                false_negative_scenarios
            ),
        },
        "result_artifacts": {
            "predictions_file": str(
                PREDICTIONS_PATH.relative_to(
                    PROJECT_ROOT
                )
            ).replace("\\", "/"),
            "predictions_sha256": (
                calculate_sha256(
                    PREDICTIONS_PATH
                )
            ),
            "scenario_results_file": str(
                SCENARIO_RESULTS_PATH.relative_to(
                    PROJECT_ROOT
                )
            ).replace("\\", "/"),
            "scenario_results_sha256": (
                calculate_sha256(
                    SCENARIO_RESULTS_PATH
                )
            ),
        },
        "model_change_prohibition": (
            "The model configuration, features and "
            "threshold must not be modified using "
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

        file_handle.write("\n")

    print(
        "Final Isolation Forest evaluation artifacts"
    )
    print("=" * 100)

    print(
        "Semantic fingerprint:",
        bundle["semantic_fingerprint"],
    )

    print(
        "Frozen threshold:",
        bundle["anomaly_threshold"],
    )

    print(
        "ROC-AUC:",
        round(roc_auc, 6),
    )

    print(
        "Average precision:",
        round(
            average_precision,
            6,
        ),
    )

    print(
        "Confusion matrix:",
        {
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn),
            "TP": int(tp),
        },
    )

    print(
        "F1 score:",
        round(f1, 6),
    )

    print(
        "Balanced accuracy:",
        round(
            balanced_accuracy,
            6,
        ),
    )

    print(
        "Medium-risk detection:",
        round(
            risk_metrics["medium"][
                "detection_rate"
            ],
            6,
        ),
    )

    print(
        "High-risk detection:",
        round(
            risk_metrics["high"][
                "detection_rate"
            ],
            6,
        ),
    )

    print("\nSaved files")
    print("-" * 100)

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
        "No model selection or threshold tuning "
        "was performed."
    )


if __name__ == "__main__":
    main()
