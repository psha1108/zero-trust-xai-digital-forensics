"""Preprocessing utilities for operational Random Forest features."""

from __future__ import annotations

from typing import Final

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.utils.validation import check_is_fitted


ROLE_COLUMN: Final[str] = "role"

ROLE_CATEGORIES: Final[list[str]] = [
    "admin",
    "employee",
    "finance_user",
    "guest",
    "hr_user",
]

NUMERIC_FEATURE_COLUMNS: Final[list[str]] = [
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

MODEL_FEATURE_COLUMNS: Final[list[str]] = [
    ROLE_COLUMN,
    *NUMERIC_FEATURE_COLUMNS,
]

BINARY_FEATURE_COLUMNS: Final[list[str]] = [
    "is_working_hour",
    "is_new_ip",
    "is_new_device",
    "is_unusual_time",
    "unauthorized_access_attempt",
    "ip_changed_during_session",
    "device_changed_during_session",
]

NON_NEGATIVE_INTEGER_COLUMNS: Final[list[str]] = [
    "failed_attempt_count",
    "access_count_5min",
    "sensitive_resource_access_count",
]

EXPECTED_TRANSFORMED_FEATURE_COLUMNS: Final[list[str]] = [
    "role_admin",
    "role_employee",
    "role_finance_user",
    "role_guest",
    "role_hr_user",
    *NUMERIC_FEATURE_COLUMNS,
]

TRANSFORMED_SOURCE_FEATURE_COLUMNS: Final[list[str]] = [
    "role",
    "role",
    "role",
    "role",
    "role",
    *NUMERIC_FEATURE_COLUMNS,
]


def _require_integral_values(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> None:
    """Require numeric columns to contain integer-valued data."""

    for column in columns:
        values = dataframe[column].to_numpy(
            dtype=np.float64,
        )

        if not np.equal(
            values,
            np.floor(values),
        ).all():
            raise ValueError(
                f"{column} must contain integer values."
            )


def select_random_forest_features(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Validate and return model features in deterministic order."""

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError(
            "Random Forest input must be a pandas DataFrame."
        )

    if dataframe.empty:
        raise ValueError(
            "Random Forest input must contain at least one row."
        )

    duplicate_columns = (
        dataframe.columns[
            dataframe.columns.duplicated()
        ]
        .astype(str)
        .tolist()
    )

    if duplicate_columns:
        raise ValueError(
            "Duplicate input columns are not allowed: "
            + ", ".join(duplicate_columns)
        )

    missing_columns = [
        column
        for column in MODEL_FEATURE_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing Random Forest model columns: "
            + ", ".join(missing_columns)
        )

    selected_df = dataframe.loc[
        :,
        MODEL_FEATURE_COLUMNS,
    ].copy()

    if selected_df[ROLE_COLUMN].isna().any():
        raise ValueError(
            "The role feature contains missing values."
        )

    selected_df[ROLE_COLUMN] = (
        selected_df[ROLE_COLUMN]
        .astype("string")
    )

    unknown_roles = sorted(
        set(
            selected_df[ROLE_COLUMN]
            .dropna()
            .astype(str)
        )
        -
        set(ROLE_CATEGORIES)
    )

    if unknown_roles:
        raise ValueError(
            "Unknown role values are not allowed: "
            + ", ".join(unknown_roles)
        )

    try:
        numeric_df = selected_df[
            NUMERIC_FEATURE_COLUMNS
        ].apply(
            pd.to_numeric,
            errors="raise",
        )
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Random Forest numeric features must contain "
            "only numeric values."
        ) from error

    if numeric_df.isna().any().any():
        raise ValueError(
            "Random Forest numeric features contain missing values."
        )

    numeric_array = numeric_df.to_numpy(
        dtype=np.float64,
    )

    if not np.isfinite(numeric_array).all():
        raise ValueError(
            "Random Forest numeric features contain "
            "infinite or non-finite values."
        )

    numeric_df = numeric_df.astype(np.float64)

    _require_integral_values(
        numeric_df,
        [
            "login_hour",
            *BINARY_FEATURE_COLUMNS,
            *NON_NEGATIVE_INTEGER_COLUMNS,
            "resource_sensitivity_score",
        ],
    )

    if not numeric_df[
        "login_hour"
    ].between(0, 23).all():
        raise ValueError(
            "login_hour must be an integer from 0 through 23."
        )

    for column in BINARY_FEATURE_COLUMNS:
        if not numeric_df[column].isin(
            [0.0, 1.0]
        ).all():
            raise ValueError(
                f"{column} must contain only 0 or 1."
            )

    for column in NON_NEGATIVE_INTEGER_COLUMNS:
        if (numeric_df[column] < 0).any():
            raise ValueError(
                f"{column} must be non-negative."
            )

    if (
        numeric_df[
            "session_duration_minutes"
        ]
        < 0
    ).any():
        raise ValueError(
            "session_duration_minutes must be non-negative."
        )

    if not numeric_df[
        "resource_sensitivity_score"
    ].isin(
        [1.0, 2.0, 3.0, 4.0]
    ).all():
        raise ValueError(
            "resource_sensitivity_score must be one of "
            "1, 2, 3, or 4."
        )

    selected_df[
        NUMERIC_FEATURE_COLUMNS
    ] = numeric_df

    return selected_df


def build_random_forest_preprocessor() -> ColumnTransformer:
    """Return an unfitted deterministic Random Forest preprocessor."""

    role_encoder = OneHotEncoder(
        categories=[ROLE_CATEGORIES],
        handle_unknown="error",
        sparse_output=False,
        dtype=np.float64,
    )

    return ColumnTransformer(
        transformers=[
            (
                "role",
                role_encoder,
                [ROLE_COLUMN],
            ),
            (
                "numeric",
                "passthrough",
                NUMERIC_FEATURE_COLUMNS,
            ),
        ],
        remainder="drop",
        sparse_threshold=0.0,
        verbose_feature_names_out=False,
    )


def get_transformed_feature_names(
    preprocessor: ColumnTransformer,
) -> list[str]:
    """Return deterministic transformed Random Forest feature names."""

    check_is_fitted(preprocessor)

    feature_names = (
        preprocessor
        .get_feature_names_out()
        .tolist()
    )

    if (
        feature_names
        != EXPECTED_TRANSFORMED_FEATURE_COLUMNS
    ):
        raise ValueError(
            "Unexpected Random Forest transformed feature schema. "
            f"Received: {feature_names}"
        )

    return feature_names


def get_transformed_source_feature_mapping(
    preprocessor: ColumnTransformer,
) -> dict[str, str]:
    """Map each transformed feature back to its source feature."""

    feature_names = get_transformed_feature_names(
        preprocessor
    )

    if len(feature_names) != len(
        TRANSFORMED_SOURCE_FEATURE_COLUMNS
    ):
        raise ValueError(
            "Random Forest transformed/source mapping length mismatch."
        )

    return dict(
        zip(
            feature_names,
            TRANSFORMED_SOURCE_FEATURE_COLUMNS,
            strict=True,
        )
    )


def transform_random_forest_features(
    preprocessor: ColumnTransformer,
    dataframe: pd.DataFrame,
) -> np.ndarray:
    """Validate and transform operational Random Forest features."""

    check_is_fitted(preprocessor)

    selected_df = select_random_forest_features(
        dataframe
    )

    transformed = np.asarray(
        preprocessor.transform(
            selected_df
        ),
        dtype=np.float64,
    )

    expected_columns = len(
        EXPECTED_TRANSFORMED_FEATURE_COLUMNS
    )

    if transformed.shape != (
        len(selected_df),
        expected_columns,
    ):
        raise ValueError(
            "Unexpected Random Forest transformed feature shape: "
            f"{transformed.shape}"
        )

    if not np.isfinite(transformed).all():
        raise ValueError(
            "Transformed Random Forest features contain "
            "non-finite values."
        )

    return transformed
