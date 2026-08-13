"""Tests for operational Random Forest inference."""

from __future__ import annotations

import copy

import numpy as np
import pandas as pd
import pytest

from ml.classification.data import (
    load_random_forest_development_data,
)
from ml.classification.inference import (
    EXPECTED_CLASS_ORDER,
    classify_operational_record,
    classify_operational_records,
    load_random_forest_bundle,
    validate_random_forest_bundle,
)
from ml.classification.preprocessing import (
    MODEL_FEATURE_COLUMNS,
    transform_random_forest_features,
)


EXPECTED_SEMANTIC_FINGERPRINT = (
    "afc34ff1b02b200b6af25ac18fbda5730"
    "86c337b26b53558bf74cbc5c4cc5824"
)


def get_development_sample(
    rows: int = 3,
) -> pd.DataFrame:
    """Return development-only records for inference tests."""

    development_df = (
        load_random_forest_development_data()
    )

    return (
        development_df
        .iloc[:rows]
        .copy()
    )


def test_saved_random_forest_bundle_loads() -> None:
    """The frozen operational RF artifact must validate."""

    bundle = load_random_forest_bundle()

    assert bundle[
        "model_name"
    ] == "operational_random_forest"

    assert bundle[
        "selected_candidate_id"
    ] == "rf_baseline"

    assert bundle[
        "class_order"
    ] == EXPECTED_CLASS_ORDER

    assert bundle[
        "semantic_fingerprint"
    ] == EXPECTED_SEMANTIC_FINGERPRINT


def test_batch_inference_returns_named_probabilities() -> None:
    """Batch inference must expose probabilities by semantic class."""

    records = get_development_sample(
        rows=4
    )

    result = classify_operational_records(
        records
    )

    assert result.index.equals(
        records.index
    )

    assert result.columns.tolist() == [
        "predicted_risk",
        "probability_low",
        "probability_medium",
        "probability_high",
    ]

    assert len(result) == 4

    assert set(
        result[
            "predicted_risk"
        ]
    ).issubset(
        {
            "low",
            "medium",
            "high",
        }
    )

    probability_columns = [
        "probability_low",
        "probability_medium",
        "probability_high",
    ]

    probabilities = result[
        probability_columns
    ].to_numpy(
        dtype=np.float64
    )

    assert np.isfinite(
        probabilities
    ).all()

    assert (
        probabilities
        >= 0.0
    ).all()

    assert (
        probabilities
        <= 1.0
    ).all()

    np.testing.assert_allclose(
        probabilities.sum(
            axis=1
        ),
        np.ones(
            len(result)
        ),
        rtol=0.0,
        atol=1e-12,
    )


def test_probability_names_respect_model_class_order() -> None:
    """Named probabilities must map from actual model.classes_."""

    bundle = load_random_forest_bundle()

    records = get_development_sample(
        rows=5
    )

    result = classify_operational_records(
        records,
        artifact_bundle=bundle,
    )

    transformed = (
        transform_random_forest_features(
            bundle[
                "preprocessor"
            ],
            records,
        )
    )

    raw_probabilities = (
        bundle[
            "model"
        ].predict_proba(
            transformed
        )
    )

    class_to_index = {
        label: index
        for index, label in enumerate(
            bundle[
                "class_order"
            ]
        )
    }

    np.testing.assert_allclose(
        result[
            "probability_low"
        ].to_numpy(),
        raw_probabilities[
            :,
            class_to_index["low"],
        ],
        rtol=0.0,
        atol=0.0,
    )

    np.testing.assert_allclose(
        result[
            "probability_medium"
        ].to_numpy(),
        raw_probabilities[
            :,
            class_to_index["medium"],
        ],
        rtol=0.0,
        atol=0.0,
    )

    np.testing.assert_allclose(
        result[
            "probability_high"
        ].to_numpy(),
        raw_probabilities[
            :,
            class_to_index["high"],
        ],
        rtol=0.0,
        atol=0.0,
    )


def test_single_record_matches_batch_inference() -> None:
    """Single-record API must agree exactly with batch inference."""

    record_df = get_development_sample(
        rows=1
    )

    record = (
        record_df[
            MODEL_FEATURE_COLUMNS
        ]
        .iloc[0]
        .to_dict()
    )

    single_result = (
        classify_operational_record(
            record
        )
    )

    batch_result = (
        classify_operational_records(
            record_df
        )
        .iloc[0]
    )

    assert (
        single_result[
            "predicted_risk"
        ]
        ==
        batch_result[
            "predicted_risk"
        ]
    )

    for probability_name in [
        "probability_low",
        "probability_medium",
        "probability_high",
    ]:
        assert (
            single_result[
                probability_name
            ]
            ==
            float(
                batch_result[
                    probability_name
                ]
            )
        )


def test_unknown_role_is_rejected_at_inference() -> None:
    """Production inference must reject unknown role categories."""

    records = get_development_sample(
        rows=1
    )

    records.loc[
        records.index[0],
        "role",
    ] = "unknown_role"

    with pytest.raises(
        ValueError,
        match="Unknown role",
    ):
        classify_operational_records(
            records
        )


def test_missing_feature_is_rejected_at_inference() -> None:
    """Inference must enforce the complete 14-feature schema."""

    records = get_development_sample(
        rows=1
    ).drop(
        columns=[
            "login_hour"
        ]
    )

    with pytest.raises(
        ValueError,
        match="Missing Random Forest model columns",
    ):
        classify_operational_records(
            records
        )


def test_non_dataframe_batch_input_is_rejected() -> None:
    """Batch inference must require a pandas DataFrame."""

    with pytest.raises(
        TypeError,
        match="pandas DataFrame",
    ):
        classify_operational_records(
            []
        )


def test_semantic_fingerprint_tampering_is_rejected() -> None:
    """A modified semantic fingerprint must invalidate the bundle."""

    bundle = load_random_forest_bundle()

    changed = copy.copy(
        bundle
    )

    changed[
        "semantic_fingerprint"
    ] = "0" * 64

    with pytest.raises(
        ValueError,
        match="semantic fingerprint mismatch",
    ):
        validate_random_forest_bundle(
            changed
        )


def test_class_order_tampering_is_rejected() -> None:
    """Probability class-order changes must invalidate the bundle."""

    bundle = load_random_forest_bundle()

    changed = copy.copy(
        bundle
    )

    changed[
        "class_order"
    ] = [
        "low",
        "medium",
        "high",
    ]

    with pytest.raises(
        ValueError,
        match="class-order contract changed",
    ):
        validate_random_forest_bundle(
            changed
        )
