"""Tests for operational Isolation Forest feature preprocessing."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.exceptions import NotFittedError

from ml.anomaly_detection.preprocessing import (
    EXPECTED_TRANSFORMED_FEATURE_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    NUMERIC_FEATURE_COLUMNS,
    ROLE_CATEGORIES,
    build_operational_preprocessor,
    get_transformed_feature_names,
    select_operational_features,
    transform_operational_features,
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


@pytest.fixture(scope="module")
def source_data() -> pd.DataFrame:
    """Load the operational synthetic dataset."""

    dataframe = pd.read_csv(DATASET_PATH)

    assert dataframe.shape == (845, 17)

    return dataframe


@pytest.fixture(scope="module")
def assignments() -> pd.DataFrame:
    """Load the deterministic partition assignments."""

    dataframe = pd.read_csv(ASSIGNMENT_PATH)

    assert dataframe.shape == (845, 7)

    return dataframe


@pytest.fixture(scope="module")
def fit_low_data(
    source_data: pd.DataFrame,
    assignments: pd.DataFrame,
) -> pd.DataFrame:
    """Return low-risk records assigned to model fitting."""

    dataframe = source_data.loc[
        assignments[
            "used_for_model_fit"
        ].eq(1)
    ].copy()

    assert dataframe.shape[0] == 362
    assert dataframe["risk_label"].eq("low").all()

    return dataframe


@pytest.fixture(scope="module")
def validation_data(
    source_data: pd.DataFrame,
    assignments: pd.DataFrame,
) -> pd.DataFrame:
    """Return validation-partition records."""

    dataframe = source_data.loc[
        assignments["partition"]
        .eq("validation")
    ].copy()

    assert dataframe.shape[0] == 138

    return dataframe


@pytest.fixture(scope="module")
def fitted_preprocessor(
    fit_low_data: pd.DataFrame,
):
    """Fit preprocessing only on normal fitting records."""

    selected_features = (
        select_operational_features(
            fit_low_data
        )
    )

    preprocessor = (
        build_operational_preprocessor()
    )

    preprocessor.fit(selected_features)

    return preprocessor


def test_preprocessing_feature_schema() -> None:
    """Source and transformed schemas must remain stable."""

    assert len(MODEL_FEATURE_COLUMNS) == 14
    assert len(NUMERIC_FEATURE_COLUMNS) == 13
    assert len(ROLE_CATEGORIES) == 5

    assert MODEL_FEATURE_COLUMNS == [
        "role",
        "login_hour",
        "is_working_hour",
        "failed_attempt_count",
        "is_new_ip",
        "is_new_device",
        "is_unusual_time",
        "session_duration_minutes",
        "resource_sensitivity_score",
        "access_count_5min",
        "unauthorized_access_attempt",
        "ip_changed_during_session",
        "device_changed_during_session",
        "sensitive_resource_access_count",
    ]

    assert len(
        EXPECTED_TRANSFORMED_FEATURE_COLUMNS
    ) == 18


def test_feature_selection_order_and_types(
    fit_low_data: pd.DataFrame,
) -> None:
    """Feature selection must exclude identifiers and metadata."""

    selected_df = (
        select_operational_features(
            fit_low_data
        )
    )

    assert selected_df.shape == (362, 14)

    assert (
        selected_df.columns.tolist()
        ==
        MODEL_FEATURE_COLUMNS
    )

    assert str(
        selected_df["role"].dtype
    ) == "string"

    assert set(
        selected_df[
            NUMERIC_FEATURE_COLUMNS
        ]
        .dtypes
        .astype(str)
    ) == {"float64"}

    assert "user_id" not in selected_df.columns
    assert "scenario_type" not in selected_df.columns
    assert "risk_label" not in selected_df.columns


def test_feature_selection_rejects_invalid_input(
    fit_low_data: pd.DataFrame,
) -> None:
    """Invalid operational inputs must fail clearly."""

    with pytest.raises(TypeError):
        select_operational_features(
            fit_low_data.to_dict(
                orient="records"
            )
        )

    with pytest.raises(ValueError):
        select_operational_features(
            fit_low_data.iloc[0:0]
        )

    missing_column_df = fit_low_data.drop(
        columns=["login_hour"]
    )

    with pytest.raises(
        ValueError,
        match="Missing operational model columns",
    ):
        select_operational_features(
            missing_column_df
        )


def test_feature_selection_rejects_bad_values(
    fit_low_data: pd.DataFrame,
) -> None:
    """Missing, textual and infinite values must be rejected."""

    missing_role_df = fit_low_data.iloc[
        [0]
    ].copy()

    missing_role_df.loc[
        missing_role_df.index[0],
        "role",
    ] = None

    with pytest.raises(
        ValueError,
        match="role feature contains missing",
    ):
        select_operational_features(
            missing_role_df
        )

    textual_numeric_df = fit_low_data.iloc[
        [0]
    ].copy()

    textual_numeric_df["login_hour"] = (
        textual_numeric_df["login_hour"]
        .astype("object")
    )

    textual_numeric_df.loc[
        textual_numeric_df.index[0],
        "login_hour",
    ] = "invalid"

    with pytest.raises(
        ValueError,
        match="only numeric values",
    ):
        select_operational_features(
            textual_numeric_df
        )

    infinite_df = fit_low_data.iloc[
        [0]
    ].copy()

    infinite_df[
        "session_duration_minutes"
    ] = (
        infinite_df[
            "session_duration_minutes"
        ].astype("float64")
    )

    infinite_df.loc[
        infinite_df.index[0],
        "session_duration_minutes",
    ] = np.inf

    with pytest.raises(
        ValueError,
        match="non-finite values",
    ):
        select_operational_features(
            infinite_df
        )


def test_unfitted_preprocessor_is_rejected(
    validation_data: pd.DataFrame,
) -> None:
    """Transformation and names require fitted preprocessing."""

    preprocessor = (
        build_operational_preprocessor()
    )

    with pytest.raises(NotFittedError):
        get_transformed_feature_names(
            preprocessor
        )

    with pytest.raises(NotFittedError):
        transform_operational_features(
            preprocessor,
            validation_data,
        )


def test_transformed_feature_names_are_stable(
    fitted_preprocessor,
) -> None:
    """One-hot and numeric output names must be deterministic."""

    feature_names = (
        get_transformed_feature_names(
            fitted_preprocessor
        )
    )

    assert (
        feature_names
        ==
        EXPECTED_TRANSFORMED_FEATURE_COLUMNS
    )

    assert feature_names[:5] == [
        "role_admin",
        "role_employee",
        "role_finance_user",
        "role_guest",
        "role_hr_user",
    ]

    assert (
        feature_names[5:]
        ==
        NUMERIC_FEATURE_COLUMNS
    )


def test_partition_transform_shapes_and_values(
    source_data: pd.DataFrame,
    assignments: pd.DataFrame,
    fit_low_data: pd.DataFrame,
    validation_data: pd.DataFrame,
    fitted_preprocessor,
) -> None:
    """All three partitions must transform to finite matrices."""

    test_data = source_data.loc[
        assignments["partition"]
        .eq("test")
    ].copy()

    fit_matrix = (
        transform_operational_features(
            fitted_preprocessor,
            fit_low_data,
        )
    )

    validation_matrix = (
        transform_operational_features(
            fitted_preprocessor,
            validation_data,
        )
    )

    test_matrix = (
        transform_operational_features(
            fitted_preprocessor,
            test_data,
        )
    )

    assert fit_matrix.shape == (362, 18)
    assert validation_matrix.shape == (138, 18)
    assert test_matrix.shape == (153, 18)

    assert fit_matrix.dtype == np.float64
    assert validation_matrix.dtype == np.float64
    assert test_matrix.dtype == np.float64

    assert np.isfinite(fit_matrix).all()
    assert np.isfinite(
        validation_matrix
    ).all()
    assert np.isfinite(test_matrix).all()


def test_known_and_unknown_role_encoding(
    fit_low_data: pd.DataFrame,
    fitted_preprocessor,
) -> None:
    """Known roles use one-hot values; unknown roles use zeros."""

    role_column_count = len(
        ROLE_CATEGORIES
    )

    known_role_df = (
        fit_low_data
        .drop_duplicates(
            subset=["role"]
        )
        .sort_values("role")
        .copy()
    )

    assert set(
        known_role_df["role"]
    ) == set(ROLE_CATEGORIES)

    known_matrix = (
        transform_operational_features(
            fitted_preprocessor,
            known_role_df,
        )
    )

    assert np.allclose(
        known_matrix[
            :,
            :role_column_count,
        ].sum(axis=1),
        1.0,
    )

    unknown_role_df = fit_low_data.iloc[
        [0]
    ].copy()

    unknown_role_df["role"] = "contractor"

    unknown_matrix = (
        transform_operational_features(
            fitted_preprocessor,
            unknown_role_df,
        )
    )

    assert unknown_matrix.shape == (1, 18)

    assert np.allclose(
        unknown_matrix[
            0,
            :role_column_count,
        ],
        0.0,
    )
