"""Tests for the final operational Isolation Forest artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from ml.anomaly_detection.fingerprinting import (
    calculate_isolation_forest_semantic_fingerprint,
)
from ml.anomaly_detection.preprocessing import (
    CONSTANT_LOW_RISK_FEATURES,
    MODEL_FEATURE_COLUMNS,
    ROLE_CATEGORIES,
    get_transformed_feature_names,
    transform_operational_features,
)
from ml.anomaly_detection.train_operational_baseline import (
    load_training_data,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "model_artifacts"
    / "operational"
    / "isolation_forest_bundle.joblib"
)

METADATA_PATH = (
    PROJECT_ROOT
    / "model_artifacts"
    / "operational"
    / "isolation_forest_metadata.json"
)

EXPECTED_SEMANTIC_FINGERPRINT = (
    "77b1dc298717107f1b1bd353d6da4a01c"
    "6fd2f00bf348a3cb4026cde0897d44e"
)

EXPECTED_THRESHOLD = 0.5532259181941123


def calculate_sha256(path: Path) -> str:
    """Return the SHA-256 checksum of a file."""

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


@pytest.fixture(scope="module")
def artifact_bundle() -> dict:
    """Load the saved model artifact once."""

    return joblib.load(MODEL_PATH)


@pytest.fixture(scope="module")
def metadata() -> dict:
    """Load the saved model metadata once."""

    with METADATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as file_handle:
        return json.load(file_handle)


@pytest.fixture(scope="module")
def development_low_df() -> pd.DataFrame:
    """Return development low-risk records only."""

    fit_low_df, validation_df = (
        load_training_data()
    )

    validation_low_df = validation_df.loc[
        validation_df["risk_label"]
        .eq("low")
    ].copy()

    dataframe = pd.concat(
        [
            fit_low_df,
            validation_low_df,
        ],
        ignore_index=True,
    )

    assert len(dataframe) == 452

    assert dataframe[
        "risk_label"
    ].eq("low").all()

    return dataframe


def test_model_artifact_files_exist() -> None:
    """The final model and metadata files must exist."""

    assert MODEL_PATH.is_file()
    assert METADATA_PATH.is_file()

    assert MODEL_PATH.stat().st_size > 0
    assert METADATA_PATH.stat().st_size > 0


def test_metadata_matches_current_artifact_checksum(
    metadata: dict,
) -> None:
    """Metadata must identify the currently saved artifact."""

    actual_checksum = calculate_sha256(
        MODEL_PATH
    )

    assert metadata[
        "artifact_sha256"
    ] == actual_checksum

    assert metadata[
        "artifact_filename"
    ] == MODEL_PATH.name


def test_artifact_schema_and_identity(
    artifact_bundle: dict,
    metadata: dict,
) -> None:
    """Artifact identity and schema must remain stable."""

    assert artifact_bundle[
        "artifact_schema_version"
    ] == 2

    assert metadata[
        "metadata_schema_version"
    ] == 2

    assert artifact_bundle[
        "model_name"
    ] == "operational_isolation_forest"

    assert artifact_bundle[
        "model_type"
    ] == "IsolationForest"

    assert metadata[
        "model_name"
    ] == artifact_bundle["model_name"]

    assert metadata[
        "model_type"
    ] == artifact_bundle["model_type"]


def test_selected_model_parameters(
    artifact_bundle: dict,
    metadata: dict,
) -> None:
    """The validated model configuration must be preserved."""

    expected_parameters = {
        "n_estimators": 300,
        "max_samples": 128,
        "max_features": 1.0,
        "contamination": "auto",
        "bootstrap": False,
        "random_state": 42,
        "n_jobs": 1,
    }

    assert artifact_bundle[
        "model_parameters"
    ] == expected_parameters

    assert metadata[
        "model_parameters"
    ] == expected_parameters

    model = artifact_bundle["model"]

    assert len(model.estimators_) == 300
    assert model.max_samples_ == 128


def test_threshold_and_calibration_contract(
    artifact_bundle: dict,
    metadata: dict,
) -> None:
    """The selected operating threshold must remain unchanged."""

    threshold = artifact_bundle[
        "anomaly_threshold"
    ]

    calibration = artifact_bundle[
        "calibration"
    ]

    assert threshold == pytest.approx(
        EXPECTED_THRESHOLD,
        rel=0.0,
        abs=1e-15,
    )

    assert calibration[
        "original_normal_rows"
    ] == 362

    assert calibration[
        "original_flagged_rows"
    ] == 45

    assert calibration[
        "final_development_normal_rows"
    ] == 452

    assert calibration[
        "final_flagged_rows"
    ] == 57

    assert calibration[
        "final_flag_rate"
    ] == pytest.approx(
        57 / 452,
        rel=0.0,
        abs=1e-15,
    )

    assert metadata[
        "calibration"
    ] == calibration


def test_semantic_fingerprint_consistency(
    artifact_bundle: dict,
    metadata: dict,
) -> None:
    """Stored and calculated semantic fingerprints must match."""

    calculated_fingerprint = (
        calculate_isolation_forest_semantic_fingerprint(
            artifact_bundle
        )
    )

    assert calculated_fingerprint == (
        EXPECTED_SEMANTIC_FINGERPRINT
    )

    assert artifact_bundle[
        "semantic_fingerprint"
    ] == calculated_fingerprint

    assert metadata[
        "semantic_fingerprint"
    ] == calculated_fingerprint


def test_feature_contract(
    artifact_bundle: dict,
) -> None:
    """The production feature schema must remain unchanged."""

    assert artifact_bundle[
        "source_feature_columns"
    ] == list(MODEL_FEATURE_COLUMNS)

    assert artifact_bundle[
        "role_categories"
    ] == list(ROLE_CATEGORIES)

    assert artifact_bundle[
        "constant_low_risk_features"
    ] == list(CONSTANT_LOW_RISK_FEATURES)

    assert len(
        artifact_bundle[
            "source_feature_columns"
        ]
    ) == 14

    assert len(
        artifact_bundle[
            "transformed_feature_columns"
        ]
    ) == 18

    loaded_feature_names = (
        get_transformed_feature_names(
            artifact_bundle[
                "preprocessor"
            ]
        )
    )

    assert loaded_feature_names == (
        artifact_bundle[
            "transformed_feature_columns"
        ]
    )


def test_development_scoring_round_trip(
    artifact_bundle: dict,
    metadata: dict,
    development_low_df: pd.DataFrame,
) -> None:
    """Loaded artifact must reproduce development scoring."""

    transformed_matrix = (
        transform_operational_features(
            artifact_bundle[
                "preprocessor"
            ],
            development_low_df,
        )
    )

    assert transformed_matrix.shape == (
        452,
        18,
    )

    assert transformed_matrix.dtype == (
        np.float64
    )

    assert np.isfinite(
        transformed_matrix
    ).all()

    scores = (
        -artifact_bundle["model"]
        .score_samples(
            transformed_matrix
        )
    )

    assert scores.shape == (452,)
    assert np.isfinite(scores).all()

    threshold = artifact_bundle[
        "anomaly_threshold"
    ]

    flagged_rows = int(
        (
            scores
            >= threshold
        ).sum()
    )

    assert flagged_rows == 57

    expected_summary = metadata[
        "development_score_summary"
    ]

    assert float(scores.min()) == pytest.approx(
        expected_summary["minimum"],
        rel=0.0,
        abs=1e-15,
    )

    assert float(np.median(scores)) == pytest.approx(
        expected_summary["median"],
        rel=0.0,
        abs=1e-15,
    )

    assert float(scores.mean()) == pytest.approx(
        expected_summary["mean"],
        rel=0.0,
        abs=1e-15,
    )

    assert float(scores.max()) == pytest.approx(
        expected_summary["maximum"],
        rel=0.0,
        abs=1e-15,
    )
