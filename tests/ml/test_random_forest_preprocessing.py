"""Tests for operational Random Forest preprocessing."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.exceptions import NotFittedError

from ml.classification.preprocessing import (
    BINARY_FEATURE_COLUMNS,
    EXPECTED_TRANSFORMED_FEATURE_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    NUMERIC_FEATURE_COLUMNS,
    ROLE_CATEGORIES,
    TRANSFORMED_SOURCE_FEATURE_COLUMNS,
    build_random_forest_preprocessor,
    get_transformed_feature_names,
    get_transformed_source_feature_mapping,
    select_random_forest_features,
    transform_random_forest_features,
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
    """Load the verified operational dataset."""

    dataframe = pd.read_csv(DATASET_PATH)

    assert dataframe.shape == (845, 17)

    return dataframe


@pytest.fixture(scope="module")
def assignments() -> pd.DataFrame:
    """Load the approved shared user-grouped assignments."""

    dataframe = pd.read_csv(ASSIGNMENT_PATH)

    assert dataframe.shape == (845, 7)

    return dataframe


@pytest.fixture(scope="module")
def fit_data(
    source_data: pd.DataFrame,
    assignments: pd.DataFrame,
) -> pd.DataFrame:
    """Return all supervised fitting records."""

    dataframe = source_data.loc[
        assignments["partition"].eq("fit")
    ].copy()

    assert len(dataframe) == 554
    assert dataframe["user_id"].nunique() == 32

    assert set(dataframe["risk_label"]) == {
        "low",
        "medium",
        "high",
    }

    return dataframe


@pytest.fixture(scope="module")
def validation_data(
    source_data: pd.DataFrame,
    assignments: pd.DataFrame,
) -> pd.DataFrame:
    """Return validation records without using final test data."""

    dataframe = source_data.loc[
        assignments["partition"].eq("validation")
    ].copy()

    assert len(dataframe) == 138
    assert dataframe["user_id"].nunique() == 8

    return dataframe


@pytest.fixture(scope="module")
def fitted_preprocessor(
    fit_data: pd.DataFrame,
):
    """Fit preprocessing using only the supervised fit partition."""

    selected = select_random_forest_features(
        fit_data
    )

    preprocessor = (
        build_random_forest_preprocessor()
    )

    preprocessor.fit(selected)

    return preprocessor


def test_feature_contract() -> None:
    """Random Forest must use the approved operational schema."""

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

    assert ROLE_CATEGORIES == [
        "admin",
        "employee",
        "finance_user",
        "guest",
        "hr_user",
    ]

    assert len(MODEL_FEATURE_COLUMNS) == 14
    assert len(NUMERIC_FEATURE_COLUMNS) == 13
    assert len(EXPECTED_TRANSFORMED_FEATURE_COLUMNS) == 18
    assert len(TRANSFORMED_SOURCE_FEATURE_COLUMNS) == 18


def test_feature_selection_order_and_types(
    fit_data: pd.DataFrame,
) -> None:
    """Identifiers, target, and scenario metadata must be excluded."""

    selected = select_random_forest_features(
        fit_data
    )

    assert selected.shape == (554, 14)

    assert (
        selected.columns.tolist()
        ==
        MODEL_FEATURE_COLUMNS
    )

    assert str(selected["role"].dtype) == "string"

    assert set(
        selected[
            NUMERIC_FEATURE_COLUMNS
        ]
        .dtypes
        .astype(str)
    ) == {"float64"}

    assert "user_id" not in selected.columns
    assert "scenario_type" not in selected.columns
    assert "risk_label" not in selected.columns


def test_invalid_input_structure_is_rejected(
    fit_data: pd.DataFrame,
) -> None:
    """Invalid containers and schemas must fail clearly."""

    with pytest.raises(
        TypeError,
        match="pandas DataFrame",
    ):
        select_random_forest_features(
            fit_data.to_dict(
                orient="records"
            )
        )

    with pytest.raises(
        ValueError,
        match="at least one row",
    ):
        select_random_forest_features(
            fit_data.iloc[0:0]
        )

    missing_df = fit_data.drop(
        columns=["login_hour"]
    )

    with pytest.raises(
        ValueError,
        match="Missing Random Forest model columns",
    ):
        select_random_forest_features(
            missing_df
        )

    duplicate_df = pd.concat(
        [
            fit_data,
            fit_data[["login_hour"]],
        ],
        axis=1,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate input columns",
    ):
        select_random_forest_features(
            duplicate_df
        )


def test_unknown_and_missing_roles_are_rejected(
    fit_data: pd.DataFrame,
) -> None:
    """Production inference must never silently encode unknown roles."""

    unknown_df = fit_data.iloc[[0]].copy()
    unknown_df["role"] = "contractor"

    with pytest.raises(
        ValueError,
        match="Unknown role values",
    ):
        select_random_forest_features(
            unknown_df
        )

    missing_df = fit_data.iloc[[0]].copy()

    missing_df.loc[
        missing_df.index[0],
        "role",
    ] = None

    with pytest.raises(
        ValueError,
        match="role feature contains missing",
    ):
        select_random_forest_features(
            missing_df
        )


def test_invalid_numeric_values_are_rejected(
    fit_data: pd.DataFrame,
) -> None:
    """Non-numeric, missing, and non-finite values must fail."""

    textual_df = fit_data.iloc[[0]].copy()
    textual_df["login_hour"] = "invalid"

    with pytest.raises(
        ValueError,
        match="only numeric values",
    ):
        select_random_forest_features(
            textual_df
        )

    missing_df = fit_data.iloc[[0]].copy()
    missing_df["session_duration_minutes"] = np.nan

    with pytest.raises(
        ValueError,
        match="contain missing values",
    ):
        select_random_forest_features(
            missing_df
        )

    infinite_df = fit_data.iloc[[0]].copy()
    infinite_df["access_count_5min"] = np.inf

    with pytest.raises(
        ValueError,
        match="non-finite values",
    ):
        select_random_forest_features(
            infinite_df
        )


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("login_hour", -1),
        ("login_hour", 24),
        ("login_hour", 12.5),
        ("is_new_ip", 2),
        ("is_new_device", -1),
        ("is_unusual_time", 0.5),
        ("failed_attempt_count", -1),
        ("failed_attempt_count", 1.5),
        ("access_count_5min", -1),
        ("sensitive_resource_access_count", -1),
        ("session_duration_minutes", -1),
        ("resource_sensitivity_score", 0),
        ("resource_sensitivity_score", 5),
        ("resource_sensitivity_score", 2.5),
    ],
)
def test_invalid_domain_values_are_rejected(
    fit_data: pd.DataFrame,
    column: str,
    value: float,
) -> None:
    """Operational feature domains must be enforced."""

    dataframe = fit_data.iloc[[0]].copy()

    dataframe[column] = value

    with pytest.raises(ValueError):
        select_random_forest_features(
            dataframe
        )


def test_binary_feature_contract(
    fit_data: pd.DataFrame,
) -> None:
    """All approved binary columns must accept only zero or one."""

    selected = select_random_forest_features(
        fit_data
    )

    for column in BINARY_FEATURE_COLUMNS:
        assert set(
            selected[column].unique()
        ).issubset({0.0, 1.0})


def test_unfitted_preprocessor_is_rejected(
    fit_data: pd.DataFrame,
) -> None:
    """Feature names and transformation require fitted preprocessing."""

    preprocessor = (
        build_random_forest_preprocessor()
    )

    with pytest.raises(NotFittedError):
        get_transformed_feature_names(
            preprocessor
        )

    with pytest.raises(NotFittedError):
        transform_random_forest_features(
            preprocessor,
            fit_data,
        )


def test_transformed_feature_contract(
    fitted_preprocessor,
) -> None:
    """Transformed feature names and source mapping must be stable."""

    names = get_transformed_feature_names(
        fitted_preprocessor
    )

    assert (
        names
        ==
        EXPECTED_TRANSFORMED_FEATURE_COLUMNS
    )

    mapping = (
        get_transformed_source_feature_mapping(
            fitted_preprocessor
        )
    )

    assert list(mapping) == names

    assert list(mapping.values()) == (
        TRANSFORMED_SOURCE_FEATURE_COLUMNS
    )

    assert mapping["role_admin"] == "role"
    assert mapping["role_guest"] == "role"

    for column in NUMERIC_FEATURE_COLUMNS:
        assert mapping[column] == column


def test_fit_and_validation_transform(
    fit_data: pd.DataFrame,
    validation_data: pd.DataFrame,
    fitted_preprocessor,
) -> None:
    """Fit and validation partitions must transform deterministically."""

    fit_matrix = (
        transform_random_forest_features(
            fitted_preprocessor,
            fit_data,
        )
    )

    validation_matrix = (
        transform_random_forest_features(
            fitted_preprocessor,
            validation_data,
        )
    )

    assert fit_matrix.shape == (554, 18)
    assert validation_matrix.shape == (138, 18)

    assert fit_matrix.dtype == np.float64
    assert validation_matrix.dtype == np.float64

    assert np.isfinite(fit_matrix).all()
    assert np.isfinite(
        validation_matrix
    ).all()


def test_role_one_hot_encoding(
    fit_data: pd.DataFrame,
    fitted_preprocessor,
) -> None:
    """Every approved role must produce exactly one active role column."""

    role_examples = (
        fit_data
        .drop_duplicates(
            subset=["role"]
        )
        .sort_values("role")
        .copy()
    )

    assert set(
        role_examples["role"]
    ) == set(ROLE_CATEGORIES)

    matrix = (
        transform_random_forest_features(
            fitted_preprocessor,
            role_examples,
        )
    )

    np.testing.assert_array_equal(
        matrix[:, :5].sum(axis=1),
        np.ones(len(role_examples)),
    )


def test_numeric_features_are_not_scaled(
    fit_data: pd.DataFrame,
    fitted_preprocessor,
) -> None:
    """Random Forest numeric inputs must be passed through unchanged."""

    sample = fit_data.head(25).copy()

    selected = select_random_forest_features(
        sample
    )

    matrix = (
        transform_random_forest_features(
            fitted_preprocessor,
            sample,
        )
    )

    expected_numeric = selected[
        NUMERIC_FEATURE_COLUMNS
    ].to_numpy(dtype=np.float64)

    actual_numeric = matrix[:, 5:]

    np.testing.assert_array_equal(
        actual_numeric,
        expected_numeric,
    )
