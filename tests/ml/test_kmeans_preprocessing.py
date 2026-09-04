"""Contract tests for operational K-Means preprocessing."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.clustering.preprocessing import (
    EXPECTED_TRANSFORMED_FEATURE_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    NUMERIC_FEATURE_COLUMNS,
    ROLE_CATEGORIES,
    ROLE_COLUMN,
    build_kmeans_preprocessor,
    get_transformed_feature_names,
    select_kmeans_features,
    transform_kmeans_features,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "ml_training_dataset.csv"
)

SPLIT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "operational"
    / "isolation_forest_split_assignments.csv"
)


EXPECTED_SOURCE_FEATURES = [
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

EXPECTED_NUMERIC_FEATURES = EXPECTED_SOURCE_FEATURES[1:]

EXPECTED_ROLES = [
    "admin",
    "employee",
    "finance_user",
    "guest",
    "hr_user",
]

EXPECTED_TRANSFORMED_FEATURES = [
    "role_admin",
    "role_employee",
    "role_finance_user",
    "role_guest",
    "role_hr_user",
    *EXPECTED_NUMERIC_FEATURES,
]


@pytest.fixture(scope="module")
def operational_dataset() -> pd.DataFrame:
    return pd.read_csv(DATASET_PATH)


@pytest.fixture(scope="module")
def split_assignments() -> pd.DataFrame:
    return pd.read_csv(SPLIT_PATH)


@pytest.fixture(scope="module")
def partitions(
    operational_dataset: pd.DataFrame,
    split_assignments: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    assert len(operational_dataset) == len(split_assignments)

    working = operational_dataset.copy()
    working["partition"] = split_assignments[
        "partition"
    ].to_numpy()

    return {
        partition: working.loc[
            working["partition"].eq(partition)
        ].copy()
        for partition in ["fit", "validation", "test"]
    }


def test_kmeans_feature_contract_is_exact() -> None:
    assert ROLE_COLUMN == "role"

    assert MODEL_FEATURE_COLUMNS == EXPECTED_SOURCE_FEATURES

    assert NUMERIC_FEATURE_COLUMNS == EXPECTED_NUMERIC_FEATURES

    assert ROLE_CATEGORIES == EXPECTED_ROLES

    assert (
        EXPECTED_TRANSFORMED_FEATURE_COLUMNS
        == EXPECTED_TRANSFORMED_FEATURES
    )

    assert len(MODEL_FEATURE_COLUMNS) == 14
    assert len(EXPECTED_TRANSFORMED_FEATURE_COLUMNS) == 18


def test_kmeans_features_exclude_identifiers_and_labels(
    operational_dataset: pd.DataFrame,
) -> None:
    selected = select_kmeans_features(
        operational_dataset
    )

    assert list(selected.columns) == EXPECTED_SOURCE_FEATURES

    for excluded in [
        "user_id",
        "scenario_type",
        "risk_label",
    ]:
        assert excluded not in selected.columns


def test_kmeans_preprocessor_has_fixed_role_encoder_and_numeric_scaler(
    partitions: dict[str, pd.DataFrame],
) -> None:
    fit_features = select_kmeans_features(
        partitions["fit"]
    )

    preprocessor = build_kmeans_preprocessor()

    assert isinstance(preprocessor, ColumnTransformer)

    preprocessor.fit(fit_features)

    role_encoder = preprocessor.named_transformers_["role"]
    numeric_scaler = preprocessor.named_transformers_["numeric"]

    assert isinstance(role_encoder, OneHotEncoder)
    assert isinstance(numeric_scaler, StandardScaler)

    assert list(role_encoder.categories_[0]) == EXPECTED_ROLES

    assert role_encoder.handle_unknown == "error"


def test_kmeans_transformed_feature_names_are_exact_and_stable(
    partitions: dict[str, pd.DataFrame],
) -> None:
    fit_features = select_kmeans_features(
        partitions["fit"]
    )

    preprocessor = build_kmeans_preprocessor()
    preprocessor.fit(fit_features)

    names = get_transformed_feature_names(
        preprocessor
    )

    assert names == EXPECTED_TRANSFORMED_FEATURES
    assert len(names) == 18


def test_shared_partitions_transform_to_finite_18_feature_matrices(
    partitions: dict[str, pd.DataFrame],
) -> None:
    fit_features = select_kmeans_features(
        partitions["fit"]
    )

    preprocessor = build_kmeans_preprocessor()
    preprocessor.fit(fit_features)

    expected_rows = {
        "fit": 554,
        "validation": 138,
        "test": 153,
    }

    for partition, expected_count in expected_rows.items():
        features = select_kmeans_features(
            partitions[partition]
        )

        transformed = transform_kmeans_features(
            preprocessor,
            features,
        )

        assert transformed.shape == (
            expected_count,
            18,
        )

        assert np.isfinite(transformed).all()


def test_numeric_features_are_standardized_using_fit_partition_only(
    partitions: dict[str, pd.DataFrame],
) -> None:
    fit_features = select_kmeans_features(
        partitions["fit"]
    )

    preprocessor = build_kmeans_preprocessor()

    transformed_fit = preprocessor.fit_transform(
        fit_features
    )

    transformed_fit = np.asarray(
        transformed_fit,
        dtype=np.float64,
    )

    # First five columns are fixed role one-hot features.
    numeric_block = transformed_fit[:, 5:]

    assert numeric_block.shape == (554, 13)

    assert np.allclose(
        numeric_block.mean(axis=0),
        0.0,
        atol=1e-10,
    )


def test_unknown_role_is_rejected_before_clustering(
    operational_dataset: pd.DataFrame,
) -> None:
    sample = operational_dataset.iloc[[0]].copy()
    sample.loc[:, "role"] = "super_admin"

    with pytest.raises(
        ValueError,
        match="Unknown role",
    ):
        select_kmeans_features(sample)


def test_missing_required_feature_is_rejected(
    operational_dataset: pd.DataFrame,
) -> None:
    sample = operational_dataset.drop(
        columns=["access_count_5min"]
    )

    with pytest.raises(
        ValueError,
        match="Missing required",
    ):
        select_kmeans_features(sample)
