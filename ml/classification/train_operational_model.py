"""Train and save the final operational Random Forest risk classifier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    log_loss,
)

from ml.classification.data import (
    ASSIGNMENT_PATH,
    DATASET_PATH,
    EXPECTED_ASSIGNMENT_CANONICAL_SHA256,
    EXPECTED_DATASET_CANONICAL_SHA256,
    calculate_canonical_text_sha256,
    load_random_forest_development_data,
)
from ml.classification.fingerprinting import (
    calculate_random_forest_metadata_semantic_fingerprint,
    calculate_random_forest_semantic_fingerprint,
)
from ml.classification.preprocessing import (
    MODEL_FEATURE_COLUMNS,
    ROLE_CATEGORIES,
    build_random_forest_preprocessor,
    get_transformed_feature_names,
    get_transformed_source_feature_mapping,
    select_random_forest_features,
    transform_random_forest_features,
)
from ml.classification.selection_protocol import (
    CANDIDATE_CONFIGURATIONS,
    get_candidate_parameters,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SELECTION_PATH = (
    PROJECT_ROOT
    / "results"
    / "metrics"
    / "operational_random_forest_selection.json"
)

ARTIFACT_DIRECTORY = (
    PROJECT_ROOT
    / "model_artifacts"
    / "operational"
)

MODEL_ARTIFACT_PATH = (
    ARTIFACT_DIRECTORY
    / "random_forest_risk_bundle.joblib"
)

MODEL_METADATA_PATH = (
    ARTIFACT_DIRECTORY
    / "random_forest_risk_metadata.json"
)

EXPECTED_SELECTED_CANDIDATE_ID = "rf_baseline"

EXPECTED_SELECTION_CANONICAL_SHA256 = (
    "da1be58595d7605aabc66459e18fc01e"
    "346d944086a4d63219ccb7e5a660014c"
)

EXPECTED_DEVELOPMENT_ROWS = 692
EXPECTED_DEVELOPMENT_USERS = 40

EXPECTED_DEVELOPMENT_LABEL_COUNTS = {
    "low": 452,
    "medium": 162,
    "high": 78,
}

REPORT_LABEL_ORDER = [
    "low",
    "medium",
    "high",
]


def calculate_sha256(path: Path) -> str:
    """Return raw file SHA-256."""

    digest = hashlib.sha256()

    with path.open("rb") as file_handle:
        for block in iter(
            lambda: file_handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def load_frozen_selection() -> tuple[
    dict,
    dict,
]:
    """Load and validate the previously frozen RF selection."""

    if not SELECTION_PATH.is_file():
        raise FileNotFoundError(
            "Frozen Random Forest selection result "
            f"was not found: {SELECTION_PATH}"
        )

    selection = json.loads(
        SELECTION_PATH.read_text(
            encoding="utf-8"
        )
    )

    if selection.get(
        "selection_status"
    ) != "validation_selection_frozen":
        raise ValueError(
            "Random Forest selection is not frozen."
        )

    if selection.get(
        "final_test_accessed"
    ) is not False:
        raise ValueError(
            "Frozen Random Forest selection indicates "
            "that the final test was accessed."
        )

    selected_candidate_id = selection.get(
        "selected_candidate_id"
    )

    if (
        selected_candidate_id
        != EXPECTED_SELECTED_CANDIDATE_ID
    ):
        raise ValueError(
            "Unexpected selected Random Forest candidate: "
            f"{selected_candidate_id}"
        )

    matching_candidates = [
        candidate
        for candidate in CANDIDATE_CONFIGURATIONS
        if candidate[
            "candidate_id"
        ] == selected_candidate_id
    ]

    if len(matching_candidates) != 1:
        raise ValueError(
            "Frozen Random Forest candidate definition "
            "could not be resolved uniquely."
        )

    expected_parameters = (
        get_candidate_parameters(
            matching_candidates[0]
        )
    )

    selected_parameters = selection.get(
        "selected_parameters"
    )

    if selected_parameters != expected_parameters:
        raise ValueError(
            "Frozen Random Forest selected parameters "
            "do not match the selection protocol."
        )

    if (
        selection.get(
            "dataset_canonical_sha256"
        )
        != EXPECTED_DATASET_CANONICAL_SHA256
    ):
        raise ValueError(
            "Frozen selection references an unexpected "
            "dataset checksum."
        )

    if (
        selection.get(
            "split_assignment_canonical_sha256"
        )
        != EXPECTED_ASSIGNMENT_CANONICAL_SHA256
    ):
        raise ValueError(
            "Frozen selection references an unexpected "
            "split-assignment checksum."
        )

    return selection, selected_parameters


def main() -> None:
    """Train and persist the final development-only classifier."""

    # ========================================================
    # 1. VERIFY FROZEN INPUT CONTRACTS
    # ========================================================

    dataset_canonical_sha256 = (
        calculate_canonical_text_sha256(
            DATASET_PATH
        )
    )

    assignment_canonical_sha256 = (
        calculate_canonical_text_sha256(
            ASSIGNMENT_PATH
        )
    )

    if (
        dataset_canonical_sha256
        != EXPECTED_DATASET_CANONICAL_SHA256
    ):
        raise ValueError(
            "Operational dataset canonical checksum mismatch."
        )

    if (
        assignment_canonical_sha256
        != EXPECTED_ASSIGNMENT_CANONICAL_SHA256
    ):
        raise ValueError(
            "Shared split-assignment canonical checksum mismatch."
        )

    selection, selected_parameters = (
        load_frozen_selection()
    )

    selection_canonical_sha256 = (
        calculate_canonical_text_sha256(
            SELECTION_PATH
        )
    )

    if (
        selection_canonical_sha256
        != EXPECTED_SELECTION_CANONICAL_SHA256
    ):
        raise ValueError(
            "Frozen Random Forest selection canonical "
            "checksum mismatch."
        )

    # ========================================================
    # 2. LOAD DEVELOPMENT DATA ONLY
    # ========================================================

    development_df = (
        load_random_forest_development_data()
    )

    if len(development_df) != EXPECTED_DEVELOPMENT_ROWS:
        raise ValueError(
            "Unexpected Random Forest development row count."
        )

    if (
        development_df[
            "user_id"
        ].nunique()
        != EXPECTED_DEVELOPMENT_USERS
    ):
        raise ValueError(
            "Unexpected Random Forest development user count."
        )

    if set(
        development_df[
            "partition"
        ]
    ) != {
        "fit",
        "validation",
    }:
        raise ValueError(
            "Final Random Forest training may use only "
            "fit and validation partitions."
        )

    development_label_counts = {
        label: int(
            development_df[
                "risk_label"
            ].eq(label).sum()
        )
        for label in REPORT_LABEL_ORDER
    }

    if (
        development_label_counts
        != EXPECTED_DEVELOPMENT_LABEL_COUNTS
    ):
        raise ValueError(
            "Unexpected Random Forest development "
            "label distribution."
        )

    # ========================================================
    # 3. FIT FINAL PREPROCESSOR
    # ========================================================

    development_features = (
        select_random_forest_features(
            development_df
        )
    )

    preprocessor = (
        build_random_forest_preprocessor()
    )

    development_matrix = np.asarray(
        preprocessor.fit_transform(
            development_features
        ),
        dtype=np.float64,
    )

    transformed_feature_columns = (
        get_transformed_feature_names(
            preprocessor
        )
    )

    transformed_source_feature_mapping = (
        get_transformed_source_feature_mapping(
            preprocessor
        )
    )

    if development_matrix.shape != (
        EXPECTED_DEVELOPMENT_ROWS,
        18,
    ):
        raise ValueError(
            "Unexpected final Random Forest transformed shape: "
            f"{development_matrix.shape}"
        )

    if not np.isfinite(
        development_matrix
    ).all():
        raise ValueError(
            "Final Random Forest development matrix "
            "contains non-finite values."
        )

    # ========================================================
    # 4. TRAIN FROZEN RANDOM FOREST
    # ========================================================

    development_target = (
        development_df[
            "risk_label"
        ]
        .astype(str)
        .to_numpy()
    )

    model = RandomForestClassifier(
        **selected_parameters
    )

    model.fit(
        development_matrix,
        development_target,
    )

    class_order = (
        np.asarray(
            model.classes_
        )
        .astype(str)
        .tolist()
    )

    expected_class_order = selection[
        "model_class_order"
    ]

    if class_order != expected_class_order:
        raise ValueError(
            "Final Random Forest class order differs "
            "from the frozen selection contract."
        )

    class_to_index = {
        label: index
        for index, label in enumerate(
            class_order
        )
    }

    if set(class_order) != set(
        REPORT_LABEL_ORDER
    ):
        raise ValueError(
            "Final Random Forest does not contain "
            "the expected risk classes."
        )

    development_predictions = np.asarray(
        model.predict(
            development_matrix
        )
    ).astype(str)

    development_probabilities = np.asarray(
        model.predict_proba(
            development_matrix
        ),
        dtype=np.float64,
    )

    if development_predictions.shape != (
        EXPECTED_DEVELOPMENT_ROWS,
    ):
        raise RuntimeError(
            "Unexpected number of development predictions."
        )

    if development_probabilities.shape != (
        EXPECTED_DEVELOPMENT_ROWS,
        len(class_order),
    ):
        raise RuntimeError(
            "Unexpected Random Forest probability shape."
        )

    if not np.isfinite(
        development_probabilities
    ).all():
        raise RuntimeError(
            "Random Forest returned non-finite probabilities."
        )

    np.testing.assert_allclose(
        development_probabilities.sum(
            axis=1
        ),
        np.ones(
            EXPECTED_DEVELOPMENT_ROWS,
            dtype=np.float64,
        ),
        rtol=0.0,
        atol=1e-12,
    )

    # ========================================================
    # 5. DEVELOPMENT TRAINING SUMMARY
    # ========================================================

    development_metrics = {
        "accuracy": float(
            accuracy_score(
                development_target,
                development_predictions,
            )
        ),
        "balanced_accuracy": float(
            balanced_accuracy_score(
                development_target,
                development_predictions,
            )
        ),
        "macro_f1": float(
            f1_score(
                development_target,
                development_predictions,
                labels=REPORT_LABEL_ORDER,
                average="macro",
                zero_division=0,
            )
        ),
        "weighted_f1": float(
            f1_score(
                development_target,
                development_predictions,
                labels=REPORT_LABEL_ORDER,
                average="weighted",
                zero_division=0,
            )
        ),
        "log_loss": float(
            log_loss(
                development_target,
                development_probabilities,
                labels=class_order,
            )
        ),
    }

    # ========================================================
    # 6. CREATE FINAL MODEL BUNDLE
    # ========================================================

    artifact_bundle = {
        "artifact_schema_version": 1,
        "model_name": (
            "operational_random_forest"
        ),
        "model_type": (
            "RandomForestClassifier"
        ),
        "selected_candidate_id": (
            EXPECTED_SELECTED_CANDIDATE_ID
        ),
        "preprocessor": preprocessor,
        "model": model,
        "source_feature_columns": list(
            MODEL_FEATURE_COLUMNS
        ),
        "transformed_feature_columns": (
            transformed_feature_columns
        ),
        "transformed_source_feature_mapping": (
            transformed_source_feature_mapping
        ),
        "role_categories": list(
            ROLE_CATEGORIES
        ),
        "class_order": class_order,
        "model_parameters": dict(
            selected_parameters
        ),
        "target_column": "risk_label",
        "probability_definition": (
            "model.predict_proba(transformed_features) "
            "with columns ordered by class_order"
        ),
    }

    semantic_fingerprint = (
        calculate_random_forest_semantic_fingerprint(
            artifact_bundle
        )
    )

    artifact_bundle[
        "semantic_fingerprint"
    ] = semantic_fingerprint

    # ========================================================
    # 7. SAVE MODEL ARTIFACT
    # ========================================================

    ARTIFACT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        artifact_bundle,
        MODEL_ARTIFACT_PATH,
        compress=3,
        protocol=5,
    )

    if not MODEL_ARTIFACT_PATH.is_file():
        raise RuntimeError(
            "Random Forest model artifact was not created."
        )

    artifact_sha256 = calculate_sha256(
        MODEL_ARTIFACT_PATH
    )

    # ========================================================
    # 8. CREATE DETERMINISTIC METADATA
    # ========================================================

    metadata = {
        "metadata_schema_version": 1,
        "model_name": (
            "operational_random_forest"
        ),
        "model_type": (
            "RandomForestClassifier"
        ),
        "artifact_filename": (
            MODEL_ARTIFACT_PATH.name
        ),
        "artifact_sha256": (
            artifact_sha256
        ),
        "semantic_fingerprint": (
            semantic_fingerprint
        ),
        "reproducibility_definition": (
            "semantic Random Forest structure, "
            "feature contract, class order and "
            "probability contract"
        ),
        "dataset_filename": (
            DATASET_PATH.name
        ),
        "dataset_canonical_sha256": (
            dataset_canonical_sha256
        ),
        "assignment_filename": (
            ASSIGNMENT_PATH.name
        ),
        "assignment_canonical_sha256": (
            assignment_canonical_sha256
        ),
        "selection_filename": (
            SELECTION_PATH.name
        ),
        "selection_canonical_sha256": (
            selection_canonical_sha256
        ),
        "training_scope": (
            "all labeled records from fit and "
            "validation partitions"
        ),
        "development_rows": (
            EXPECTED_DEVELOPMENT_ROWS
        ),
        "development_users": (
            EXPECTED_DEVELOPMENT_USERS
        ),
        "development_label_counts": (
            development_label_counts
        ),
        "source_feature_count": len(
            MODEL_FEATURE_COLUMNS
        ),
        "transformed_feature_count": len(
            transformed_feature_columns
        ),
        "source_feature_columns": list(
            MODEL_FEATURE_COLUMNS
        ),
        "transformed_feature_columns": (
            transformed_feature_columns
        ),
        "transformed_source_feature_mapping": (
            transformed_source_feature_mapping
        ),
        "role_categories": list(
            ROLE_CATEGORIES
        ),
        "selected_candidate_id": (
            EXPECTED_SELECTED_CANDIDATE_ID
        ),
        "model_parameters": dict(
            selected_parameters
        ),
        "class_order": class_order,
        "class_to_index": class_to_index,
        "report_label_order": list(
            REPORT_LABEL_ORDER
        ),
        "development_training_metrics": (
            development_metrics
        ),
        "final_test_accessed": False,
        "software_versions": {
            "python_implementation": (
                platform.python_implementation()
            ),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": (
                sklearn.__version__
            ),
            "joblib": joblib.__version__,
        },
    }

    metadata_semantic_fingerprint = (
        calculate_random_forest_metadata_semantic_fingerprint(
            metadata
        )
    )

    metadata[
        "metadata_semantic_fingerprint"
    ] = metadata_semantic_fingerprint

    with MODEL_METADATA_PATH.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file_handle:
        json.dump(
            metadata,
            file_handle,
            indent=2,
            sort_keys=True,
        )
        file_handle.write("\n")

    if not MODEL_METADATA_PATH.is_file():
        raise RuntimeError(
            "Random Forest metadata was not created."
        )

    metadata_sha256 = calculate_sha256(
        MODEL_METADATA_PATH
    )

    # ========================================================
    # 9. ROUND-TRIP ARTIFACT VERIFICATION
    # ========================================================

    loaded_bundle = joblib.load(
        MODEL_ARTIFACT_PATH
    )

    if loaded_bundle[
        "artifact_schema_version"
    ] != 1:
        raise RuntimeError(
            "Unexpected Random Forest artifact schema "
            "after round trip."
        )

    if loaded_bundle[
        "semantic_fingerprint"
    ] != semantic_fingerprint:
        raise RuntimeError(
            "Stored Random Forest semantic fingerprint "
            "changed after round trip."
        )

    if (
        calculate_random_forest_semantic_fingerprint(
            loaded_bundle
        )
        != semantic_fingerprint
    ):
        raise RuntimeError(
            "Reloaded Random Forest semantic identity "
            "does not match."
        )

    reloaded_matrix = (
        transform_random_forest_features(
            loaded_bundle[
                "preprocessor"
            ],
            development_df,
        )
    )

    reloaded_predictions = np.asarray(
        loaded_bundle[
            "model"
        ].predict(
            reloaded_matrix
        )
    ).astype(str)

    reloaded_probabilities = np.asarray(
        loaded_bundle[
            "model"
        ].predict_proba(
            reloaded_matrix
        ),
        dtype=np.float64,
    )

    np.testing.assert_allclose(
        reloaded_matrix,
        development_matrix,
        rtol=0.0,
        atol=0.0,
    )

    np.testing.assert_array_equal(
        reloaded_predictions,
        development_predictions,
    )

    np.testing.assert_allclose(
        reloaded_probabilities,
        development_probabilities,
        rtol=0.0,
        atol=0.0,
    )

    round_trip_max_probability_difference = float(
        np.max(
            np.abs(
                reloaded_probabilities
                -
                development_probabilities
            )
        )
    )

    # ========================================================
    # 10. OUTPUT
    # ========================================================

    print(
        "Final operational Random Forest artifact"
    )
    print("=" * 100)

    print(
        "Development rows:",
        EXPECTED_DEVELOPMENT_ROWS,
    )

    print(
        "Development users:",
        EXPECTED_DEVELOPMENT_USERS,
    )

    print(
        "Development label counts:",
        development_label_counts,
    )

    print(
        "Selected candidate:",
        EXPECTED_SELECTED_CANDIDATE_ID,
    )

    print(
        "Transformed feature count:",
        len(
            transformed_feature_columns
        ),
    )

    print(
        "Class order:",
        class_order,
    )

    print(
        "Class-to-index mapping:",
        class_to_index,
    )

    print(
        "\nDevelopment training metrics"
    )
    print("-" * 100)

    for metric_name, metric_value in (
        development_metrics.items()
    ):
        print(
            f"{metric_name}:",
            round(
                metric_value,
                12,
            ),
        )

    print(
        "\nSaved artifacts"
    )
    print("-" * 100)

    print(
        "Model artifact:",
        MODEL_ARTIFACT_PATH.relative_to(
            PROJECT_ROOT
        ),
    )

    print(
        "Model artifact size:",
        MODEL_ARTIFACT_PATH.stat().st_size,
        "bytes",
    )

    print(
        "Model artifact SHA256:",
        artifact_sha256,
    )

    print(
        "Model semantic fingerprint:",
        semantic_fingerprint,
    )

    print(
        "Metadata:",
        MODEL_METADATA_PATH.relative_to(
            PROJECT_ROOT
        ),
    )

    print(
        "Metadata SHA256:",
        metadata_sha256,
    )

    print(
        "Metadata semantic fingerprint:",
        metadata_semantic_fingerprint,
    )

    print(
        "\nRound-trip maximum probability difference:",
        round_trip_max_probability_difference,
    )

    print(
        "\nFinal test accessed:",
        False,
    )

    print(
        "\nFinal Random Forest development training "
        "and round-trip verification passed."
    )


if __name__ == "__main__":
    main()
