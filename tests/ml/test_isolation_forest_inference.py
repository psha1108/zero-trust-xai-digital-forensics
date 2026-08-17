"""Tests for operational Isolation Forest inference."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.api.types import (
    is_bool_dtype,
    is_float_dtype,
)

from ml.anomaly_detection.inference import (
    DEFAULT_MODEL_PATH,
    load_isolation_forest_bundle,
    score_operational_record,
    score_operational_records,
    validate_isolation_forest_bundle,
)
from ml.anomaly_detection.preprocessing import (
    transform_operational_features,
)
from ml.anomaly_detection.train_operational_baseline import (
    load_training_data,
)


@pytest.fixture(scope="module")
def artifact_bundle() -> dict:
    """Load the validated production artifact."""

    return load_isolation_forest_bundle()


@pytest.fixture(scope="module")
def sample_records() -> pd.DataFrame:
    """Return development fitting records only."""

    fit_low_df, _ = load_training_data()

    records = fit_low_df.head(12).copy()

    assert len(records) == 12
    assert records[
        "risk_label"
    ].eq("low").all()

    return records


def test_default_artifact_loads_and_validates(
    artifact_bundle: dict,
) -> None:
    """The default production artifact must load successfully."""

    assert DEFAULT_MODEL_PATH.is_file()

    assert artifact_bundle[
        "artifact_schema_version"
    ] == 2

    assert artifact_bundle[
        "model_name"
    ] == "operational_isolation_forest"

    validate_isolation_forest_bundle(
        artifact_bundle
    )


def test_batch_scoring_output_contract(
    artifact_bundle: dict,
    sample_records: pd.DataFrame,
) -> None:
    """Batch inference must return the documented schema."""

    results = score_operational_records(
        sample_records,
        artifact_bundle=artifact_bundle,
    )

    assert results.shape == (12, 4)

    assert results.columns.tolist() == [
        "anomaly_score",
        "anomaly_threshold",
        "threshold_margin",
        "is_anomaly",
    ]

    assert results.index.equals(
        sample_records.index
    )

    assert is_float_dtype(
        results["anomaly_score"]
    )

    assert is_float_dtype(
        results["anomaly_threshold"]
    )

    assert is_float_dtype(
        results["threshold_margin"]
    )

    assert is_bool_dtype(
        results["is_anomaly"]
    )

    assert np.isfinite(
        results[
            [
                "anomaly_score",
                "anomaly_threshold",
                "threshold_margin",
            ]
        ].to_numpy()
    ).all()


def test_batch_scores_match_direct_model_scoring(
    artifact_bundle: dict,
    sample_records: pd.DataFrame,
) -> None:
    """Inference scores must match direct artifact scoring."""

    transformed_matrix = (
        transform_operational_features(
            artifact_bundle[
                "preprocessor"
            ],
            sample_records,
        )
    )

    expected_scores = (
        -artifact_bundle["model"]
        .score_samples(
            transformed_matrix
        )
    )

    results = score_operational_records(
        sample_records,
        artifact_bundle=artifact_bundle,
    )

    np.testing.assert_array_equal(
        results[
            "anomaly_score"
        ].to_numpy(),
        expected_scores,
    )


def test_threshold_margin_and_prediction_logic(
    artifact_bundle: dict,
    sample_records: pd.DataFrame,
) -> None:
    """Margins and predictions must use the saved threshold."""

    results = score_operational_records(
        sample_records,
        artifact_bundle=artifact_bundle,
    )

    threshold = artifact_bundle[
        "anomaly_threshold"
    ]

    expected_margins = (
        results[
            "anomaly_score"
        ].to_numpy()
        -
        threshold
    )

    expected_predictions = (
        results[
            "anomaly_score"
        ].to_numpy()
        >=
        threshold
    )

    np.testing.assert_array_equal(
        results[
            "anomaly_threshold"
        ].to_numpy(),
        np.full(
            len(sample_records),
            threshold,
            dtype=np.float64,
        ),
    )

    np.testing.assert_array_equal(
        results[
            "threshold_margin"
        ].to_numpy(),
        expected_margins,
    )

    np.testing.assert_array_equal(
        results[
            "is_anomaly"
        ].to_numpy(),
        expected_predictions,
    )


def test_single_record_matches_batch_scoring(
    artifact_bundle: dict,
    sample_records: pd.DataFrame,
) -> None:
    """Single-record inference must match batch inference."""

    record = sample_records.iloc[
        0
    ].to_dict()

    single_result = (
        score_operational_record(
            record,
            artifact_bundle=artifact_bundle,
        )
    )

    batch_result = (
        score_operational_records(
            sample_records.iloc[
                [0]
            ],
            artifact_bundle=artifact_bundle,
        )
        .iloc[0]
    )

    assert single_result[
        "anomaly_score"
    ] == float(
        batch_result[
            "anomaly_score"
        ]
    )

    assert single_result[
        "anomaly_threshold"
    ] == float(
        batch_result[
            "anomaly_threshold"
        ]
    )

    assert single_result[
        "threshold_margin"
    ] == float(
        batch_result[
            "threshold_margin"
        ]
    )

    assert single_result[
        "is_anomaly"
    ] is bool(
        batch_result[
            "is_anomaly"
        ]
    )


def test_loading_from_explicit_model_path() -> None:
    """Inference must support an explicitly supplied artifact path."""

    bundle = load_isolation_forest_bundle(
        DEFAULT_MODEL_PATH
    )

    assert bundle[
        "semantic_fingerprint"
    ] == (
        "77b1dc298717107f1b1bd353d6da4a01c"
        "6fd2f00bf348a3cb4026cde0897d44e"
    )


def test_missing_model_path_is_rejected(
    tmp_path: Path,
) -> None:
    """A missing model artifact must produce a clear error."""

    missing_path = (
        tmp_path
        / "missing_model.joblib"
    )

    with pytest.raises(
        FileNotFoundError,
        match="artifact was not found",
    ):
        load_isolation_forest_bundle(
            missing_path
        )


def test_batch_scoring_rejects_invalid_input_type(
    artifact_bundle: dict,
) -> None:
    """Batch scoring requires a pandas DataFrame."""

    with pytest.raises(
        TypeError,
        match="pandas DataFrame",
    ):
        score_operational_records(
            [],
            artifact_bundle=artifact_bundle,
        )


def test_batch_scoring_rejects_empty_dataframe(
    artifact_bundle: dict,
) -> None:
    """Batch scoring requires at least one record."""

    with pytest.raises(
        ValueError,
        match="At least one",
    ):
        score_operational_records(
            pd.DataFrame(),
            artifact_bundle=artifact_bundle,
        )


def test_single_scoring_rejects_non_mapping(
    artifact_bundle: dict,
) -> None:
    """Single-record scoring requires mapping input."""

    with pytest.raises(
        TypeError,
        match="provided as a mapping",
    ):
        score_operational_record(
            ["invalid"],
            artifact_bundle=artifact_bundle,
        )


def test_tampered_semantic_fingerprint_is_rejected(
    artifact_bundle: dict,
) -> None:
    """Artifact validation must reject fingerprint tampering."""

    tampered_bundle = dict(
        artifact_bundle
    )

    tampered_bundle[
        "semantic_fingerprint"
    ] = "0" * 64

    with pytest.raises(
        ValueError,
        match="semantic fingerprint mismatch",
    ):
        validate_isolation_forest_bundle(
            tampered_bundle
        )
