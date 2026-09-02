"""Preprocessing contract for operational K-Means clustering."""

from __future__ import annotations

from typing import Final

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


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

EXPECTED_TRANSFORMED_FEATURE_COLUMNS: Final[list[str]] = [
    "role_admin",
    "role_employee",
    "role_finance_user",
    "role_guest",
    "role_hr_user",
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


def _validate_required_columns(
    dataframe: pd.DataFrame,
) -> None:
    """Require every approved operational source feature."""

    missing = [
        column
        for column in MODEL_FEATURE_COLUMNS
        if column not in dataframe.columns
    ]

    if missing:
        raise ValueError(
            "Missing required K-Means feature columns: "
            + ", ".join(missing)
        )


def _validate_role_feature(
    selected_df: pd.DataFrame,
) -> None:
    """Validate the fixed operational role contract."""

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
        - set(ROLE_CATEGORIES)
    )

    if unknown_roles:
        raise ValueError(
            "Unknown role values are not allowed: "
            + ", ".join(unknown_roles)
        )


def _coerce_and_validate_numeric_features(
    selected_df: pd.DataFrame,
) -> None:
    """Coerce numeric inputs and enforce operational constraints."""

    try:
        numeric_df = selected_df[
            NUMERIC_FEATURE_COLUMNS
        ].apply(
            pd.to_numeric,
            errors="raise",
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "K-Means numeric features must contain only numeric values."
        ) from exc

    if numeric_df.isna().any().any():
        raise ValueError(
            "K-Means numeric features contain missing values."
        )

    numeric_values = numeric_df.to_numpy(
        dtype=np.float64,
    )

    if not np.isfinite(numeric_values).all():
        raise ValueError(
            "K-Means numeric features must be finite."
        )

    if not numeric_df["login_hour"].between(
        0,
        23,
    ).all():
        raise ValueError(
            "login_hour must be between 0 and 23."
        )

    if not np.allclose(
        numeric_df["login_hour"],
        np.round(numeric_df["login_hour"]),
    ):
        raise ValueError(
            "login_hour must contain integer values."
        )

    for column in BINARY_FEATURE_COLUMNS:
        if not numeric_df[column].isin(
            [0, 1]
        ).all():
            raise ValueError(
                f"{column} must contain only 0 or 1."
            )

    for column in NON_NEGATIVE_INTEGER_COLUMNS:
        if (numeric_df[column] < 0).any():
            raise ValueError(
                f"{column} must be non-negative."
            )

        if not np.allclose(
            numeric_df[column],
            np.round(numeric_df[column]),
        ):
            raise ValueError(
                f"{column} must contain integer values."
            )

    if (
        numeric_df["session_duration_minutes"] < 0
    ).any():
        raise ValueError(
            "session_duration_minutes must be non-negative."
        )

    if not numeric_df[
        "resource_sensitivity_score"
    ].isin(
        [1, 2, 3, 4]
    ).all():
        raise ValueError(
            "resource_sensitivity_score must be one of "
            "1, 2, 3, or 4."
        )

    for column in NUMERIC_FEATURE_COLUMNS:
        selected_df[column] = numeric_df[column]


def select_kmeans_features(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Select and validate the exact 14 operational K-Means inputs.

    Identifiers, scenario metadata, and risk labels are deliberately
    excluded from behavioral clustering.
    """

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError(
            "K-Means input must be a pandas DataFrame."
        )

    _validate_required_columns(dataframe)

    selected_df = dataframe[
        MODEL_FEATURE_COLUMNS
    ].copy()

    _validate_role_feature(selected_df)

    _coerce_and_validate_numeric_features(
        selected_df
    )

    return selected_df


def build_kmeans_preprocessor() -> ColumnTransformer:
    """
    Build the frozen K-Means preprocessing pipeline.

    Role is one-hot encoded using five fixed application roles.
    Numeric behavioral features are standardized because K-Means
    uses Euclidean distance.
    """

    role_encoder = OneHotEncoder(
        categories=[ROLE_CATEGORIES],
        handle_unknown="error",
        sparse_output=False,
        dtype=np.float64,
    )

    numeric_scaler = StandardScaler()

    return ColumnTransformer(
        transformers=[
            (
                "role",
                role_encoder,
                [ROLE_COLUMN],
            ),
            (
                "numeric",
                numeric_scaler,
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
    """Return the exact frozen 18-feature transformed schema."""

    names = list(
        preprocessor.get_feature_names_out()
    )

    if names != EXPECTED_TRANSFORMED_FEATURE_COLUMNS:
        raise ValueError(
            "K-Means transformed feature contract changed. "
            f"Expected {EXPECTED_TRANSFORMED_FEATURE_COLUMNS}, "
            f"got {names}."
        )

    return names


def transform_kmeans_features(
    preprocessor: ColumnTransformer,
    dataframe: pd.DataFrame,
) -> np.ndarray:
    """Validate and transform operational records for K-Means."""

    selected_df = select_kmeans_features(
        dataframe
    )

    transformed = preprocessor.transform(
        selected_df
    )

    transformed = np.asarray(
        transformed,
        dtype=np.float64,
    )

    expected_shape = (
        len(selected_df),
        len(EXPECTED_TRANSFORMED_FEATURE_COLUMNS),
    )

    if transformed.shape != expected_shape:
        raise ValueError(
            "Unexpected K-Means transformed matrix shape: "
            f"{transformed.shape}; expected {expected_shape}."
        )

    if not np.isfinite(transformed).all():
        raise ValueError(
            "K-Means transformed features contain non-finite values."
        )

    return transformed
