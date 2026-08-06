"""Train and save the final operational Isolation Forest artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest

from ml.anomaly_detection.fingerprinting import (
    calculate_isolation_forest_semantic_fingerprint,
)
from ml.anomaly_detection.preprocessing import (
    CONSTANT_LOW_RISK_FEATURES,
    MODEL_FEATURE_COLUMNS,
    ROLE_CATEGORIES,
    build_operational_preprocessor,
    get_transformed_feature_names,
    select_operational_features,
    transform_operational_features,
)
from ml.anomaly_detection.train_operational_baseline import (
    MAX_SAMPLES,
    N_ESTIMATORS,
    RANDOM_STATE,
    load_training_data,
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

ARTIFACT_DIRECTORY = (
    PROJECT_ROOT
    / "model_artifacts"
    / "operational"
)

MODEL_ARTIFACT_PATH = (
    ARTIFACT_DIRECTORY
    / "isolation_forest_bundle.joblib"
)

MODEL_METADATA_PATH = (
    ARTIFACT_DIRECTORY
    / "isolation_forest_metadata.json"
)


MAX_FEATURES = 1.0

SELECTED_VALIDATION_THRESHOLD = (
    0.554034390894
)

CALIBRATION_FIT_ROWS = 362
CALIBRATION_FLAGGED_ROWS = 45

EXPECTED_DEVELOPMENT_LOW_ROWS = 452
EXPECTED_TRANSFERRED_FLAGGED_ROWS = 57
EXPECTED_TRANSFERRED_THRESHOLD = (
    0.553225918194
)


def calculate_sha256(path: Path) -> str:
    """Return a file SHA-256 checksum."""

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


def main() -> None:
    """Train, calibrate and save the final model bundle."""

    # ========================================================
    # 1. LOAD DEVELOPMENT PARTITIONS
    # ========================================================

    fit_low_df, validation_df = (
        load_training_data()
    )

    validation_low_df = validation_df.loc[
        validation_df["risk_label"]
        .eq("low")
    ].copy()

    development_low_df = pd.concat(
        [
            fit_low_df,
            validation_low_df,
        ],
        ignore_index=True,
    )

    assert len(fit_low_df) == 362
    assert len(validation_low_df) == 90
    assert len(development_low_df) == 452

    assert development_low_df[
        "risk_label"
    ].eq("low").all()

    # ========================================================
    # 2. FIT PREPROCESSOR
    # ========================================================

    development_features = (
        select_operational_features(
            development_low_df
        )
    )

    preprocessor = (
        build_operational_preprocessor()
    )

    development_matrix = np.asarray(
        preprocessor.fit_transform(
            development_features
        ),
        dtype=np.float64,
    )

    transformed_feature_names = (
        get_transformed_feature_names(
            preprocessor
        )
    )

    assert development_matrix.shape == (
        452,
        18,
    )

    assert np.isfinite(
        development_matrix
    ).all()

    # ========================================================
    # 3. TRAIN FINAL ISOLATION FOREST
    # ========================================================

    model = IsolationForest(
        n_estimators=N_ESTIMATORS,
        max_samples=MAX_SAMPLES,
        contamination="auto",
        max_features=MAX_FEATURES,
        bootstrap=False,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )

    model.fit(development_matrix)

    development_scores = (
        -model.score_samples(
            development_matrix
        )
    )

    assert np.isfinite(
        development_scores
    ).all()

    # ========================================================
    # 4. TRANSFER THE VALIDATED NORMAL FLAG RATE
    # ========================================================

    calibration_flag_rate = (
        CALIBRATION_FLAGGED_ROWS
        /
        CALIBRATION_FIT_ROWS
    )

    calibration_quantile = (
        1.0
        -
        calibration_flag_rate
    )

    anomaly_threshold = float(
        np.quantile(
            development_scores,
            calibration_quantile,
            method="higher",
        )
    )

    development_flagged_rows = int(
        (
            development_scores
            >= anomaly_threshold
        ).sum()
    )

    development_flag_rate = (
        development_flagged_rows
        /
        len(development_scores)
    )

    assert np.isclose(
        anomaly_threshold,
        EXPECTED_TRANSFERRED_THRESHOLD,
        rtol=0.0,
        atol=1e-12,
    )

    assert (
        development_flagged_rows
        ==
        EXPECTED_TRANSFERRED_FLAGGED_ROWS
    )

    # ========================================================
    # 5. CREATE MODEL BUNDLE
    # ========================================================

    artifact_bundle = {
        "artifact_schema_version": 2,
        "model_name": (
            "operational_isolation_forest"
        ),
        "model_type": "IsolationForest",
        "preprocessor": preprocessor,
        "model": model,
        "anomaly_threshold": (
            anomaly_threshold
        ),
        "score_definition": (
            "-model.score_samples("
            "transformed_features)"
        ),
        "score_direction": (
            "higher_is_more_anomalous"
        ),
        "source_feature_columns": list(
            MODEL_FEATURE_COLUMNS
        ),
        "transformed_feature_columns": (
            transformed_feature_names
        ),
        "role_categories": list(
            ROLE_CATEGORIES
        ),
        "constant_low_risk_features": list(
            CONSTANT_LOW_RISK_FEATURES
        ),
        "model_parameters": {
            "n_estimators": N_ESTIMATORS,
            "max_samples": MAX_SAMPLES,
            "max_features": MAX_FEATURES,
            "contamination": "auto",
            "bootstrap": False,
            "random_state": RANDOM_STATE,
            "n_jobs": 1,
        },
        "calibration": {
            "selected_validation_threshold": (
                SELECTED_VALIDATION_THRESHOLD
            ),
            "original_normal_rows": (
                CALIBRATION_FIT_ROWS
            ),
            "original_flagged_rows": (
                CALIBRATION_FLAGGED_ROWS
            ),
            "normal_flag_rate": (
                calibration_flag_rate
            ),
            "transferred_quantile": (
                calibration_quantile
            ),
            "final_development_normal_rows": (
                len(development_low_df)
            ),
            "final_anomaly_threshold": (
                anomaly_threshold
            ),
            "final_flagged_rows": (
                development_flagged_rows
            ),
            "final_flag_rate": (
                development_flag_rate
            ),
        },
    }

    semantic_fingerprint = (
        calculate_isolation_forest_semantic_fingerprint(
            artifact_bundle
        )
    )

    artifact_bundle[
        "semantic_fingerprint"
    ] = semantic_fingerprint

    # ========================================================
    # 6. SAVE MODEL ARTIFACT
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

    assert MODEL_ARTIFACT_PATH.exists()

    model_artifact_sha256 = (
        calculate_sha256(
            MODEL_ARTIFACT_PATH
        )
    )

    # ========================================================
    # 7. SAVE DETERMINISTIC METADATA
    # ========================================================

    metadata = {
        "metadata_schema_version": 2,
        "model_name": (
            "operational_isolation_forest"
        ),
        "model_type": "IsolationForest",
        "artifact_filename": (
            MODEL_ARTIFACT_PATH.name
        ),
        "artifact_sha256": (
            model_artifact_sha256
        ),
        "semantic_fingerprint": (
            semantic_fingerprint
        ),
        "reproducibility_definition": (
            "semantic model structure, transformed "
            "scores, predictions and threshold"
        ),
        "dataset_filename": (
            DATASET_PATH.name
        ),
        "dataset_sha256": calculate_sha256(
            DATASET_PATH
        ),
        "assignment_filename": (
            ASSIGNMENT_PATH.name
        ),
        "assignment_sha256": (
            calculate_sha256(
                ASSIGNMENT_PATH
            )
        ),
        "training_scope": (
            "low-risk records from fit and "
            "validation partitions"
        ),
        "development_low_risk_rows": (
            len(development_low_df)
        ),
        "source_feature_count": len(
            MODEL_FEATURE_COLUMNS
        ),
        "transformed_feature_count": len(
            transformed_feature_names
        ),
        "source_feature_columns": list(
            MODEL_FEATURE_COLUMNS
        ),
        "transformed_feature_columns": (
            transformed_feature_names
        ),
        "constant_low_risk_features": list(
            CONSTANT_LOW_RISK_FEATURES
        ),
        "model_parameters": (
            artifact_bundle[
                "model_parameters"
            ]
        ),
        "calibration": (
            artifact_bundle[
                "calibration"
            ]
        ),
        "development_score_summary": {
            "minimum": float(
                development_scores.min()
            ),
            "median": float(
                np.median(
                    development_scores
                )
            ),
            "mean": float(
                development_scores.mean()
            ),
            "maximum": float(
                development_scores.max()
            ),
        },
        "software_versions": {
            "python_implementation": (
                "CPython"
            ),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": (
                sklearn.__version__
            ),
            "joblib": joblib.__version__,
        },
    }

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

    assert MODEL_METADATA_PATH.exists()

    metadata_sha256 = calculate_sha256(
        MODEL_METADATA_PATH
    )

    # ========================================================
    # 8. ROUND-TRIP ARTIFACT VERIFICATION
    # ========================================================

    loaded_bundle = joblib.load(
        MODEL_ARTIFACT_PATH
    )

    assert loaded_bundle[
        "artifact_schema_version"
    ] == 2

    assert loaded_bundle[
        "source_feature_columns"
    ] == list(MODEL_FEATURE_COLUMNS)

    assert np.isclose(
        loaded_bundle[
            "anomaly_threshold"
        ],
        anomaly_threshold,
        rtol=0.0,
        atol=0.0,
    )

    assert loaded_bundle[
        "semantic_fingerprint"
    ] == semantic_fingerprint

    assert (
        calculate_isolation_forest_semantic_fingerprint(
            loaded_bundle
        )
        ==
        semantic_fingerprint
    )

    reloaded_matrix = (
        transform_operational_features(
            loaded_bundle[
                "preprocessor"
            ],
            development_low_df,
        )
    )

    reloaded_scores = (
        -loaded_bundle[
            "model"
        ].score_samples(
            reloaded_matrix
        )
    )

    np.testing.assert_allclose(
        reloaded_matrix,
        development_matrix,
        rtol=0.0,
        atol=0.0,
    )

    np.testing.assert_allclose(
        reloaded_scores,
        development_scores,
        rtol=0.0,
        atol=0.0,
    )

    round_trip_max_score_difference = (
        float(
            np.max(
                np.abs(
                    reloaded_scores
                    -
                    development_scores
                )
            )
        )
    )

    # ========================================================
    # 9. OUTPUT
    # ========================================================

    print(
        "Final operational Isolation Forest artifact"
    )
    print("=" * 100)

    print(
        "Development low-risk rows:",
        len(development_low_df),
    )

    print(
        "Transformed feature count:",
        len(transformed_feature_names),
    )

    print(
        "Number of estimators:",
        N_ESTIMATORS,
    )

    print(
        "Maximum samples:",
        MAX_SAMPLES,
    )

    print(
        "Calibration normal flag rate:",
        round(
            calibration_flag_rate,
            9,
        ),
    )

    print(
        "Transferred threshold:",
        round(
            anomaly_threshold,
            12,
        ),
    )

    print(
        "Development rows flagged:",
        development_flagged_rows,
    )

    print(
        "Development flag rate:",
        round(
            development_flag_rate,
            9,
        ),
    )

    print("\nDevelopment score summary")
    print("-" * 100)

    print(
        "Minimum:",
        round(
            float(
                development_scores.min()
            ),
            12,
        ),
    )

    print(
        "Median:",
        round(
            float(
                np.median(
                    development_scores
                )
            ),
            12,
        ),
    )

    print(
        "Mean:",
        round(
            float(
                development_scores.mean()
            ),
            12,
        ),
    )

    print(
        "Maximum:",
        round(
            float(
                development_scores.max()
            ),
            12,
        ),
    )

    print("\nSaved artifacts")
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
        model_artifact_sha256,
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
        "Semantic fingerprint:",
        semantic_fingerprint,
    )

    print(
        "\nRound-trip maximum score difference:",
        round_trip_max_score_difference,
    )

    print(
        "\nFinal model artifact training and "
        "round-trip verification passed."
    )


if __name__ == "__main__":
    main()
