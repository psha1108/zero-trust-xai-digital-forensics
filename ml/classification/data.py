"""Data and partition contract for operational Random Forest training."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Final

import pandas as pd


PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

DATASET_PATH: Final[Path] = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "ml_training_dataset.csv"
)

ASSIGNMENT_PATH: Final[Path] = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "operational"
    / "isolation_forest_split_assignments.csv"
)

EXPECTED_DATASET_CANONICAL_SHA256: Final[str] = (
    "b93e093189a130f2c7d953ff66cedd9c"
    "fcb8cfa2321b5c0c4475e68962ddff15"
)

EXPECTED_ASSIGNMENT_CANONICAL_SHA256: Final[str] = (
    "96efcbc2b8097287b83b1ef289b46e73"
    "3bbd49bfff6d9d166a6b646c765e91ea"
)

EXPECTED_DATASET_SHAPE: Final[tuple[int, int]] = (
    845,
    17,
)

EXPECTED_ASSIGNMENT_SHAPE: Final[tuple[int, int]] = (
    845,
    7,
)

EXPECTED_PARTITION_ROWS: Final[dict[str, int]] = {
    "fit": 554,
    "validation": 138,
    "test": 153,
}

EXPECTED_PARTITION_USERS: Final[dict[str, int]] = {
    "fit": 32,
    "validation": 8,
    "test": 10,
}

RISK_LABELS: Final[list[str]] = [
    "low",
    "medium",
    "high",
]


def calculate_canonical_text_sha256(
    path: Path,
) -> str:
    """Return SHA-256 after canonical LF line-ending normalization."""

    if not path.is_file():
        raise FileNotFoundError(
            f"Required text artifact was not found: {path}"
        )

    raw_bytes = path.read_bytes()

    canonical_bytes = (
        raw_bytes
        .replace(b"\r\n", b"\n")
        .replace(b"\r", b"\n")
    )

    return hashlib.sha256(
        canonical_bytes
    ).hexdigest()


def _validate_source_and_assignments(
    dataframe: pd.DataFrame,
    assignments: pd.DataFrame,
) -> None:
    """Validate the shared grouped partition contract."""

    if dataframe.shape != EXPECTED_DATASET_SHAPE:
        raise ValueError(
            "Unexpected operational dataset shape: "
            f"{dataframe.shape}"
        )

    if assignments.shape != EXPECTED_ASSIGNMENT_SHAPE:
        raise ValueError(
            "Unexpected split-assignment shape: "
            f"{assignments.shape}"
        )

    expected_indices = list(
        range(len(dataframe))
    )

    if (
        assignments[
            "source_row_index"
        ].tolist()
        != expected_indices
    ):
        raise ValueError(
            "Split assignments are not aligned "
            "with source-row order."
        )

    for column in [
        "user_id",
        "role",
        "risk_label",
        "scenario_type",
    ]:
        pd.testing.assert_series_equal(
            dataframe[column].reset_index(
                drop=True
            ),
            assignments[column].reset_index(
                drop=True
            ),
            check_names=False,
            check_dtype=False,
        )

    partition_rows = (
        assignments["partition"]
        .value_counts()
        .to_dict()
    )

    if partition_rows != EXPECTED_PARTITION_ROWS:
        raise ValueError(
            "Unexpected partition row counts: "
            f"{partition_rows}"
        )

    partition_users = (
        assignments.groupby(
            "partition"
        )["user_id"]
        .nunique()
        .to_dict()
    )

    if partition_users != EXPECTED_PARTITION_USERS:
        raise ValueError(
            "Unexpected partition user counts: "
            f"{partition_users}"
        )

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

    if (
        users_by_partition["fit"]
        & users_by_partition["validation"]
    ):
        raise ValueError(
            "User leakage exists between fit and validation."
        )

    if (
        users_by_partition["fit"]
        & users_by_partition["test"]
    ):
        raise ValueError(
            "User leakage exists between fit and test."
        )

    if (
        users_by_partition["validation"]
        & users_by_partition["test"]
    ):
        raise ValueError(
            "User leakage exists between validation and test."
        )


def load_random_forest_selection_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    """Return fit and validation data for model selection.

    The final test partition is deliberately not returned by this
    model-selection loader.
    """

    dataset_checksum = (
        calculate_canonical_text_sha256(
            DATASET_PATH
        )
    )

    if (
        dataset_checksum
        != EXPECTED_DATASET_CANONICAL_SHA256
    ):
        raise ValueError(
            "Operational dataset canonical checksum mismatch."
        )

    assignment_checksum = (
        calculate_canonical_text_sha256(
            ASSIGNMENT_PATH
        )
    )

    if (
        assignment_checksum
        != EXPECTED_ASSIGNMENT_CANONICAL_SHA256
    ):
        raise ValueError(
            "Shared split-assignment canonical checksum mismatch."
        )

    dataframe = pd.read_csv(
        DATASET_PATH
    )

    assignments = pd.read_csv(
        ASSIGNMENT_PATH
    )

    _validate_source_and_assignments(
        dataframe,
        assignments,
    )

    working_df = dataframe.copy()

    working_df[
        "source_row_index"
    ] = assignments[
        "source_row_index"
    ].to_numpy()

    working_df[
        "partition"
    ] = assignments[
        "partition"
    ].to_numpy()

    fit_df = working_df.loc[
        working_df[
            "partition"
        ].eq("fit")
    ].copy()

    validation_df = working_df.loc[
        working_df[
            "partition"
        ].eq("validation")
    ].copy()

    if len(fit_df) != 554:
        raise ValueError(
            "Expected 554 Random Forest fit rows."
        )

    if len(validation_df) != 138:
        raise ValueError(
            "Expected 138 Random Forest validation rows."
        )

    if fit_df["user_id"].nunique() != 32:
        raise ValueError(
            "Expected 32 users in Random Forest fit data."
        )

    if validation_df["user_id"].nunique() != 8:
        raise ValueError(
            "Expected 8 users in Random Forest validation data."
        )

    if set(fit_df["risk_label"]) != set(
        RISK_LABELS
    ):
        raise ValueError(
            "Random Forest fit data does not contain "
            "all expected target labels."
        )

    if set(
        validation_df["risk_label"]
    ) != set(RISK_LABELS):
        raise ValueError(
            "Random Forest validation data does not contain "
            "all expected target labels."
        )

    if (
        set(fit_df["user_id"])
        & set(validation_df["user_id"])
    ):
        raise ValueError(
            "User leakage exists between Random Forest "
            "fit and validation data."
        )

    return fit_df, validation_df
