"""Preprocessing utilities for operational Isolation Forest features."""

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

CONSTANT_LOW_RISK_FEATURES: Final[list[str]] = [
    "is_unusual_time",
    "ip_changed_during_session",
    "device_changed_during_session",
]

EXPECTED_TRANSFORMED_FEATURE_COLUMNS: Final[list[str]] = [
    "role_admin",
    "role_employee",
    "role_finance_user",
    "role_guest",
    "role_hr_user",
    *NUMERIC_FEATURE_COLUMNS,
]


def select_operational_features(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Validate and return model features in deterministic order."""

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError(
            "Operational model input must be a pandas DataFrame."
        )

    if dataframe.empty:
        raise ValueError(
            "Operational model input must contain at least one row."
        )

    missing_columns = [
        column
        for column in MODEL_FEATURE_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing operational model columns: "
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

    try:
        numeric_df = selected_df[
            NUMERIC_FEATURE_COLUMNS
        ].apply(
            pd.to_numeric,
            errors="raise",
        )
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Operational numeric features must contain "
            "only numeric values."
        ) from error

    if numeric_df.isna().any().any():
        raise ValueError(
            "Operational numeric features contain missing values."
        )

    numeric_array = numeric_df.to_numpy(
        dtype=np.float64,
    )

    if not np.isfinite(numeric_array).all():
        raise ValueError(
            "Operational numeric features contain "
            "infinite or non-finite values."
        )

    selected_df[
        NUMERIC_FEATURE_COLUMNS
    ] = numeric_df.astype(np.float64)

    return selected_df


def build_operational_preprocessor() -> ColumnTransformer:
    """Return an unfitted deterministic feature preprocessor."""

    role_encoder = OneHotEncoder(
        categories=[ROLE_CATEGORIES],
        handle_unknown="ignore",
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
    """Return deterministic transformed feature names."""

    check_is_fitted(preprocessor)

    feature_names = (
        preprocessor
        .get_feature_names_out()
        .tolist()
    )

    if feature_names != EXPECTED_TRANSFORMED_FEATURE_COLUMNS:
        raise ValueError(
            "Unexpected transformed feature schema. "
            f"Received: {feature_names}"
        )

    return feature_names


def transform_operational_features(
    preprocessor: ColumnTransformer,
    dataframe: pd.DataFrame,
) -> np.ndarray:
    """Validate and transform operational model features."""

    check_is_fitted(preprocessor)

    selected_df = select_operational_features(
        dataframe
    )

    transformed = np.asarray(
        preprocessor.transform(selected_df),
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
            "Unexpected transformed feature shape: "
            f"{transformed.shape}"
        )

    if not np.isfinite(transformed).all():
        raise ValueError(
            "Transformed operational features contain "
            "non-finite values."
        )

    return transformed
