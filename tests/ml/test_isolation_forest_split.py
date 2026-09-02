"""Tests for deterministic operational Isolation Forest data splitting."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest


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

METADATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "operational"
    / "isolation_forest_split_metadata.json"
)


EXPECTED_DATASET_SHA256 = (
    "6447c2bdbbc939eaf97d21bc5b2bd70a"
    "290a067d9bcf5847511c1c47c9ac869d"
)

EXPECTED_ASSIGNMENT_SHA256 = (
    "3b04239a1bade6f6815d472b5f6b5b5f"
    "e98df7eeabb1ccbc264ceefcbb17c138"
)

EXPECTED_METADATA_SHA256 = (
    "578b932cdaabdaf6a761eb80065a865b"
    "aed412ea4cbdf333421eeb6876be60a3"
)

EXPECTED_COLUMNS = [
    "source_row_index",
    "user_id",
    "role",
    "risk_label",
    "scenario_type",
    "partition",
    "used_for_model_fit",
]

EXPECTED_MODEL_FEATURES = [
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


def calculate_sha256(path: Path) -> str:
    """Return a file SHA-256 checksum."""

    digest = hashlib.sha256()

    with path.open("rb") as file_handle:
        for block in iter(
            lambda: file_handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


@pytest.fixture(scope="module")
def assignments() -> pd.DataFrame:
    """Load saved split assignments."""

    return pd.read_csv(ASSIGNMENT_PATH)


@pytest.fixture(scope="module")
def metadata() -> dict:
    """Load saved split metadata."""

    with METADATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as file_handle:
        return json.load(file_handle)


def test_split_artifact_files_exist() -> None:
    """Required source and generated files must exist."""

    assert DATASET_PATH.exists()
    assert ASSIGNMENT_PATH.exists()
    assert METADATA_PATH.exists()


def test_split_artifact_checksums() -> None:
    """Generated split artifacts must remain reproducible."""

    assert (
        calculate_sha256(DATASET_PATH)
        ==
        EXPECTED_DATASET_SHA256
    )

    assert (
        calculate_sha256(ASSIGNMENT_PATH)
        ==
        EXPECTED_ASSIGNMENT_SHA256
    )

    assert (
        calculate_sha256(METADATA_PATH)
        ==
        EXPECTED_METADATA_SHA256
    )


def test_assignment_schema_and_source_rows(
    assignments: pd.DataFrame,
) -> None:
    """Every source row must receive exactly one assignment."""

    assert assignments.shape == (845, 7)
    assert assignments.columns.tolist() == EXPECTED_COLUMNS
    assert assignments.isna().sum().sum() == 0

    assert assignments[
        "source_row_index"
    ].is_unique

    assert assignments[
        "source_row_index"
    ].tolist() == list(range(845))


def test_partition_row_and_user_counts(
    assignments: pd.DataFrame,
) -> None:
    """Partition sizes must match the verified grouped split."""

    assert (
        assignments["partition"]
        .value_counts()
        .to_dict()
    ) == {
        "fit": 554,
        "validation": 138,
        "test": 153,
    }

    assert (
        assignments.groupby(
            "partition"
        )["user_id"]
        .nunique()
        .to_dict()
    ) == {
        "fit": 32,
        "validation": 8,
        "test": 10,
    }


def test_model_fit_marker(
    assignments: pd.DataFrame,
) -> None:
    """Only low-risk fit-partition rows may train the model."""

    expected_marker = (
        assignments["partition"].eq("fit")
        &
        assignments["risk_label"].eq("low")
    ).astype("int64")

    pd.testing.assert_series_equal(
        assignments[
            "used_for_model_fit"
        ].astype("int64"),
        expected_marker,
        check_names=False,
    )

    assert int(
        assignments[
            "used_for_model_fit"
        ].sum()
    ) == 362


def test_users_do_not_cross_partitions(
    assignments: pd.DataFrame,
) -> None:
    """No user may appear in more than one partition."""

    users_by_partition = {
        partition: set(
            assignments.loc[
                assignments[
                    "partition"
                ].eq(partition),
                "user_id",
            ]
        )
        for partition in [
            "fit",
            "validation",
            "test",
        ]
    }

    assert not (
        users_by_partition["fit"]
        &
        users_by_partition["validation"]
    )

    assert not (
        users_by_partition["fit"]
        &
        users_by_partition["test"]
    )

    assert not (
        users_by_partition["validation"]
        &
        users_by_partition["test"]
    )


def test_split_metadata(
    metadata: dict,
) -> None:
    """Metadata must describe the verified split exactly."""

    assert metadata[
        "metadata_schema_version"
    ] == 1

    assert metadata[
        "dataset_sha256"
    ] == EXPECTED_DATASET_SHA256

    assert metadata["total_rows"] == 845
    assert metadata["total_users"] == 50

    assert metadata[
        "model_feature_columns"
    ] == EXPECTED_MODEL_FEATURES

    assert metadata[
        "excluded_model_columns"
    ] == [
        "user_id",
        "scenario_type",
        "risk_label",
    ]

    assert metadata["outer_split"] == {
        "random_state": 42,
        "n_splits": 5,
        "selected_fold": 1,
    }

    assert metadata["inner_split"] == {
        "random_state": 43,
        "n_splits": 5,
        "selected_fold": 3,
    }

    assert metadata["user_overlap"] == {
        "fit_validation": 0,
        "fit_test": 0,
        "validation_test": 0,
    }

    assert metadata["partitions"]["fit"][
        "low_risk_rows_used_for_fit"
    ] == 362
