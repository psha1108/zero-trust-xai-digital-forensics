"""Reproduce and persist operational Random Forest model selection."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    log_loss,
    precision_recall_fscore_support,
)

from ml.classification.data import (
    EXPECTED_ASSIGNMENT_CANONICAL_SHA256,
    EXPECTED_DATASET_CANONICAL_SHA256,
    load_random_forest_selection_data,
)
from ml.classification.preprocessing import (
    build_random_forest_preprocessor,
    select_random_forest_features,
    transform_random_forest_features,
)
from ml.classification.selection_protocol import (
    CANDIDATE_CONFIGURATIONS,
    PRIMARY_SELECTION_METRIC,
    SECONDARY_SELECTION_METRIC,
    TERTIARY_SELECTION_METRIC,
    get_candidate_parameters,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RESULT_DIRECTORY = (
    PROJECT_ROOT
    / "results"
    / "metrics"
)

CANDIDATE_RESULTS_PATH = (
    RESULT_DIRECTORY
    / "operational_random_forest_validation_candidates.csv"
)

SELECTION_METADATA_PATH = (
    RESULT_DIRECTORY
    / "operational_random_forest_selection.json"
)

REPORT_LABEL_ORDER = [
    "low",
    "medium",
    "high",
]

EXPECTED_SELECTED_CANDIDATE = "rf_baseline"


def main() -> None:
    """Evaluate frozen candidates and persist the selection decision."""

    fit_df, validation_df = (
        load_random_forest_selection_data()
    )

    fit_features = (
        select_random_forest_features(
            fit_df
        )
    )

    preprocessor = (
        build_random_forest_preprocessor()
    )

    fit_matrix = np.asarray(
        preprocessor.fit_transform(
            fit_features
        ),
        dtype=np.float64,
    )

    validation_matrix = (
        transform_random_forest_features(
            preprocessor,
            validation_df,
        )
    )

    y_fit = fit_df[
        "risk_label"
    ].to_numpy()

    y_validation = validation_df[
        "risk_label"
    ].to_numpy()

    results: list[dict] = []

    model_class_order: list[str] | None = None

    for candidate in CANDIDATE_CONFIGURATIONS:
        candidate_id = candidate[
            "candidate_id"
        ]

        parameters = (
            get_candidate_parameters(
                candidate
            )
        )

        model = RandomForestClassifier(
            **parameters
        )

        model.fit(
            fit_matrix,
            y_fit,
        )

        predictions = model.predict(
            validation_matrix
        )

        probabilities = (
            model.predict_proba(
                validation_matrix
            )
        )

        current_class_order = (
            model.classes_
            .astype(str)
            .tolist()
        )

        if model_class_order is None:
            model_class_order = (
                current_class_order
            )
        elif (
            current_class_order
            != model_class_order
        ):
            raise RuntimeError(
                "Random Forest candidate class order changed."
            )

        precision, recall, class_f1, support = (
            precision_recall_fscore_support(
                y_validation,
                predictions,
                labels=REPORT_LABEL_ORDER,
                zero_division=0,
            )
        )

        results.append(
            {
                "candidate_id": candidate_id,
                "macro_f1": float(
                    f1_score(
                        y_validation,
                        predictions,
                        average="macro",
                    )
                ),
                "balanced_accuracy": float(
                    balanced_accuracy_score(
                        y_validation,
                        predictions,
                    )
                ),
                "log_loss": float(
                    log_loss(
                        y_validation,
                        probabilities,
                        labels=model.classes_,
                    )
                ),
                "accuracy": float(
                    accuracy_score(
                        y_validation,
                        predictions,
                    )
                ),
                "weighted_f1": float(
                    f1_score(
                        y_validation,
                        predictions,
                        average="weighted",
                    )
                ),
                "validation_errors": int(
                    (
                        predictions
                        != y_validation
                    ).sum()
                ),
                "low_precision": float(
                    precision[0]
                ),
                "low_recall": float(
                    recall[0]
                ),
                "low_f1": float(
                    class_f1[0]
                ),
                "low_support": int(
                    support[0]
                ),
                "medium_precision": float(
                    precision[1]
                ),
                "medium_recall": float(
                    recall[1]
                ),
                "medium_f1": float(
                    class_f1[1]
                ),
                "medium_support": int(
                    support[1]
                ),
                "high_precision": float(
                    precision[2]
                ),
                "high_recall": float(
                    recall[2]
                ),
                "high_f1": float(
                    class_f1[2]
                ),
                "high_support": int(
                    support[2]
                ),
            }
        )

    results_df = pd.DataFrame(
        results
    )

    ranked = (
        results_df
        .sort_values(
            by=[
                PRIMARY_SELECTION_METRIC,
                SECONDARY_SELECTION_METRIC,
                TERTIARY_SELECTION_METRIC,
            ],
            ascending=[
                False,
                False,
                True,
            ],
            kind="stable",
        )
        .reset_index(
            drop=True
        )
    )

    ranked.insert(
        0,
        "rank",
        range(
            1,
            len(ranked) + 1,
        ),
    )

    selected_candidate_id = str(
        ranked.loc[
            0,
            "candidate_id",
        ]
    )

    if (
        selected_candidate_id
        != EXPECTED_SELECTED_CANDIDATE
    ):
        raise RuntimeError(
            "Frozen Random Forest selection changed. "
            f"Received: {selected_candidate_id}"
        )

    selected_candidate = next(
        candidate
        for candidate in CANDIDATE_CONFIGURATIONS
        if candidate[
            "candidate_id"
        ] == selected_candidate_id
    )

    selected_parameters = (
        get_candidate_parameters(
            selected_candidate
        )
    )

    RESULT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    ranked.to_csv(
        CANDIDATE_RESULTS_PATH,
        index=False,
        lineterminator="\n",
    )

    selection_metadata = {
        "selection_schema_version": 1,
        "model_name": (
            "operational_random_forest"
        ),
        "model_type": (
            "RandomForestClassifier"
        ),
        "selection_status": (
            "validation_selection_frozen"
        ),
        "final_test_accessed": False,
        "fit_rows": int(
            len(fit_df)
        ),
        "fit_users": int(
            fit_df[
                "user_id"
            ].nunique()
        ),
        "validation_rows": int(
            len(validation_df)
        ),
        "validation_users": int(
            validation_df[
                "user_id"
            ].nunique()
        ),
        "dataset_canonical_sha256": (
            EXPECTED_DATASET_CANONICAL_SHA256
        ),
        "split_assignment_canonical_sha256": (
            EXPECTED_ASSIGNMENT_CANONICAL_SHA256
        ),
        "candidate_count": int(
            len(
                CANDIDATE_CONFIGURATIONS
            )
        ),
        "selection_priority": [
            {
                "metric": (
                    PRIMARY_SELECTION_METRIC
                ),
                "direction": "maximize",
            },
            {
                "metric": (
                    SECONDARY_SELECTION_METRIC
                ),
                "direction": "maximize",
            },
            {
                "metric": (
                    TERTIARY_SELECTION_METRIC
                ),
                "direction": "minimize",
            },
        ],
        "selected_candidate_id": (
            selected_candidate_id
        ),
        "selected_parameters": (
            selected_parameters
        ),
        "model_class_order": (
            model_class_order
        ),
        "report_label_order": (
            REPORT_LABEL_ORDER
        ),
        "selected_validation_metrics": {
            key: (
                int(ranked.loc[0, key])
                if key
                in {
                    "validation_errors",
                    "low_support",
                    "medium_support",
                    "high_support",
                }
                else float(
                    ranked.loc[
                        0,
                        key,
                    ]
                )
            )
            for key in [
                "macro_f1",
                "balanced_accuracy",
                "log_loss",
                "accuracy",
                "weighted_f1",
                "validation_errors",
                "low_precision",
                "low_recall",
                "low_f1",
                "low_support",
                "medium_precision",
                "medium_recall",
                "medium_f1",
                "medium_support",
                "high_precision",
                "high_recall",
                "high_f1",
                "high_support",
            ]
        },
        "selection_rationale": (
            "All frozen candidates produced identical "
            "macro F1 and balanced accuracy on validation; "
            "rf_baseline had the lowest validation log loss "
            "under the predeclared tertiary selection metric."
        ),
    }

    with SELECTION_METADATA_PATH.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file_handle:
        json.dump(
            selection_metadata,
            file_handle,
            indent=2,
            sort_keys=True,
        )
        file_handle.write("\n")

    print(
        "Random Forest validation selection persisted"
    )
    print("=" * 80)

    print(
        "Selected candidate:",
        selected_candidate_id,
    )

    print(
        "Model classes_:",
        model_class_order,
    )

    print(
        "Macro F1:",
        round(
            float(
                ranked.loc[
                    0,
                    "macro_f1",
                ]
            ),
            6,
        ),
    )

    print(
        "Balanced accuracy:",
        round(
            float(
                ranked.loc[
                    0,
                    "balanced_accuracy",
                ]
            ),
            6,
        ),
    )

    print(
        "Log loss:",
        round(
            float(
                ranked.loc[
                    0,
                    "log_loss",
                ]
            ),
            6,
        ),
    )

    print(
        "Candidate results:",
        CANDIDATE_RESULTS_PATH.relative_to(
            PROJECT_ROOT
        ),
    )

    print(
        "Selection metadata:",
        SELECTION_METADATA_PATH.relative_to(
            PROJECT_ROOT
        ),
    )

    print(
        "Final test accessed:",
        False,
    )


if __name__ == "__main__":
    main()
