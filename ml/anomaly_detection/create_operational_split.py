"""Create the deterministic operational Isolation Forest data split."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "ml_training_dataset.csv"
)

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "operational"
)

ASSIGNMENT_PATH = (
    OUTPUT_DIRECTORY
    / "isolation_forest_split_assignments.csv"
)

METADATA_PATH = (
    OUTPUT_DIRECTORY
    / "isolation_forest_split_metadata.json"
)


MODEL_FEATURE_COLUMNS = [
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

EXCLUDED_MODEL_COLUMNS = [
    "user_id",
    "scenario_type",
    "risk_label",
]

LABEL_ORDER = [
    "low",
    "medium",
    "high",
]

ROLE_ORDER = [
    "admin",
    "employee",
    "finance_user",
    "guest",
    "hr_user",
]

OUTER_RANDOM_STATE = 42
OUTER_N_SPLITS = 5
OUTER_SELECTED_FOLD = 1

INNER_RANDOM_STATE = 43
INNER_N_SPLITS = 5
INNER_SELECTED_FOLD = 3


def calculate_sha256(path: Path) -> str:
    """Return the SHA-256 checksum of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as file_handle:
        for block in iter(
            lambda: file_handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def value_counts_dict(
    dataframe: pd.DataFrame,
    column: str,
    order: list[str],
) -> dict[str, int]:
    """Return ordered integer value counts."""

    counts = (
        dataframe[column]
        .value_counts()
        .reindex(order, fill_value=0)
    )

    return {
        str(key): int(value)
        for key, value in counts.items()
    }


def main() -> None:
    """Create and validate deterministic split assignments."""

    dataframe = pd.read_csv(DATASET_PATH)

    assert dataframe.shape == (845, 17)
    assert dataframe["user_id"].nunique() == 50
    assert dataframe.isna().sum().sum() == 0

    assert set(
        dataframe["risk_label"].unique()
    ) == set(LABEL_ORDER)

    assert set(
        dataframe["role"].unique()
    ) == set(ROLE_ORDER)

    assert (
        dataframe.groupby("user_id")["role"]
        .nunique()
        .max()
        == 1
    )

    # --------------------------------------------------------
    # Outer development/test split
    # --------------------------------------------------------

    outer_splitter = StratifiedGroupKFold(
        n_splits=OUTER_N_SPLITS,
        shuffle=True,
        random_state=OUTER_RANDOM_STATE,
    )

    outer_splits = list(
        outer_splitter.split(
            X=dataframe[MODEL_FEATURE_COLUMNS],
            y=dataframe["risk_label"],
            groups=dataframe["user_id"],
        )
    )

    development_indices, test_indices = outer_splits[
        OUTER_SELECTED_FOLD - 1
    ]

    development_df = dataframe.iloc[
        development_indices
    ].copy()

    test_df = dataframe.iloc[
        test_indices
    ].copy()

    # --------------------------------------------------------
    # Inner fit/validation split
    # --------------------------------------------------------

    inner_splitter = StratifiedGroupKFold(
        n_splits=INNER_N_SPLITS,
        shuffle=True,
        random_state=INNER_RANDOM_STATE,
    )

    inner_splits = list(
        inner_splitter.split(
            X=development_df[
                MODEL_FEATURE_COLUMNS
            ],
            y=development_df["risk_label"],
            groups=development_df["user_id"],
        )
    )

    fit_positions, validation_positions = inner_splits[
        INNER_SELECTED_FOLD - 1
    ]

    fit_df = development_df.iloc[
        fit_positions
    ].copy()

    validation_df = development_df.iloc[
        validation_positions
    ].copy()

    fit_low_df = fit_df.loc[
        fit_df["risk_label"].eq("low")
    ].copy()

    # --------------------------------------------------------
    # User-separation validation
    # --------------------------------------------------------

    fit_users = set(fit_df["user_id"])
    validation_users = set(
        validation_df["user_id"]
    )
    test_users = set(test_df["user_id"])

    fit_validation_overlap = (
        fit_users & validation_users
    )

    fit_test_overlap = fit_users & test_users

    validation_test_overlap = (
        validation_users & test_users
    )

    assert not fit_validation_overlap
    assert not fit_test_overlap
    assert not validation_test_overlap

    assert set(fit_low_df["role"]) == set(
        ROLE_ORDER
    )

    assert set(validation_df["role"]) == set(
        ROLE_ORDER
    )

    assert set(test_df["role"]) == set(
        ROLE_ORDER
    )

    assert set(
        validation_df["risk_label"]
    ) == set(LABEL_ORDER)

    assert set(
        test_df["risk_label"]
    ) == set(LABEL_ORDER)

    # Protect the already verified split.
    assert len(fit_df) == 554
    assert len(validation_df) == 138
    assert len(test_df) == 153

    assert len(fit_users) == 32
    assert len(validation_users) == 8
    assert len(test_users) == 10

    assert len(fit_low_df) == 362

    # --------------------------------------------------------
    # Build one assignment record per source row
    # --------------------------------------------------------

    partition_by_index = pd.Series(
        index=dataframe.index,
        dtype="string",
    )

    partition_by_index.loc[
        fit_df.index
    ] = "fit"

    partition_by_index.loc[
        validation_df.index
    ] = "validation"

    partition_by_index.loc[
        test_df.index
    ] = "test"

    assert partition_by_index.notna().all()

    assignment_df = pd.DataFrame({
        "source_row_index": dataframe.index,
        "user_id": dataframe["user_id"],
        "role": dataframe["role"],
        "risk_label": dataframe["risk_label"],
        "scenario_type": dataframe[
            "scenario_type"
        ],
        "partition": partition_by_index,
    })

    assignment_df["used_for_model_fit"] = (
        assignment_df["partition"]
        .eq("fit")
        &
        assignment_df["risk_label"]
        .eq("low")
    ).astype("uint8")

    assert len(assignment_df) == len(dataframe)

    assert assignment_df[
        "source_row_index"
    ].is_unique

    assert assignment_df[
        "source_row_index"
    ].tolist() == list(range(len(dataframe)))

    assert int(
        assignment_df[
            "used_for_model_fit"
        ].sum()
    ) == 362

    # --------------------------------------------------------
    # Save assignments and metadata
    # --------------------------------------------------------

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    assignment_df.to_csv(
        ASSIGNMENT_PATH,
        index=False,
    )

    metadata = {
        "dataset": DATASET_PATH.name,
        "dataset_sha256": calculate_sha256(
            DATASET_PATH
        ),
        "metadata_schema_version": 1,
        "total_rows": int(len(dataframe)),
        "total_users": int(
            dataframe["user_id"].nunique()
        ),
        "model_feature_columns": (
            MODEL_FEATURE_COLUMNS
        ),
        "excluded_model_columns": (
            EXCLUDED_MODEL_COLUMNS
        ),
        "split_strategy": (
            "nested deterministic "
            "StratifiedGroupKFold by user_id"
        ),
        "outer_split": {
            "random_state": OUTER_RANDOM_STATE,
            "n_splits": OUTER_N_SPLITS,
            "selected_fold": (
                OUTER_SELECTED_FOLD
            ),
        },
        "inner_split": {
            "random_state": INNER_RANDOM_STATE,
            "n_splits": INNER_N_SPLITS,
            "selected_fold": (
                INNER_SELECTED_FOLD
            ),
        },
        "partitions": {
            "fit": {
                "rows": int(len(fit_df)),
                "users": int(len(fit_users)),
                "risk_distribution": (
                    value_counts_dict(
                        fit_df,
                        "risk_label",
                        LABEL_ORDER,
                    )
                ),
                "role_distribution": (
                    value_counts_dict(
                        fit_df,
                        "role",
                        ROLE_ORDER,
                    )
                ),
                "low_risk_rows_used_for_fit": (
                    int(len(fit_low_df))
                ),
            },
            "validation": {
                "rows": int(
                    len(validation_df)
                ),
                "users": int(
                    len(validation_users)
                ),
                "risk_distribution": (
                    value_counts_dict(
                        validation_df,
                        "risk_label",
                        LABEL_ORDER,
                    )
                ),
                "role_distribution": (
                    value_counts_dict(
                        validation_df,
                        "role",
                        ROLE_ORDER,
                    )
                ),
            },
            "test": {
                "rows": int(len(test_df)),
                "users": int(len(test_users)),
                "risk_distribution": (
                    value_counts_dict(
                        test_df,
                        "risk_label",
                        LABEL_ORDER,
                    )
                ),
                "role_distribution": (
                    value_counts_dict(
                        test_df,
                        "role",
                        ROLE_ORDER,
                    )
                ),
            },
        },
        "user_overlap": {
            "fit_validation": int(
                len(fit_validation_overlap)
            ),
            "fit_test": int(
                len(fit_test_overlap)
            ),
            "validation_test": int(
                len(validation_test_overlap)
            ),
        },
    }

    with METADATA_PATH.open(
        "w",
        encoding="utf-8",
    ) as file_handle:
        json.dump(
            metadata,
            file_handle,
            indent=2,
        )

    assert ASSIGNMENT_PATH.exists()
    assert METADATA_PATH.exists()

    assignment_dtypes = {
        "source_row_index": "int64",
        "user_id": "string",
        "role": "string",
        "risk_label": "string",
        "scenario_type": "string",
        "partition": "string",
        "used_for_model_fit": "uint8",
    }

    saved_assignment_df = pd.read_csv(
        ASSIGNMENT_PATH,
        dtype=assignment_dtypes,
    )

    expected_assignment_df = (
        assignment_df
        .astype(assignment_dtypes)
        .reset_index(drop=True)
    )

    saved_assignment_df = (
        saved_assignment_df
        .reset_index(drop=True)
    )

    pd.testing.assert_frame_equal(
        saved_assignment_df,
        expected_assignment_df,
        check_dtype=True,
        check_exact=True,
    )

    print("Operational split artifacts created")
    print("=" * 80)

    print(
        "Dataset SHA256:",
        metadata["dataset_sha256"],
    )

    print("\nPartition row counts")
    print(
        assignment_df["partition"]
        .value_counts()
        .reindex(
            [
                "fit",
                "validation",
                "test",
            ]
        )
        .to_string()
    )

    print("\nPartition user counts")
    print(
        assignment_df.groupby(
            "partition"
        )["user_id"]
        .nunique()
        .reindex(
            [
                "fit",
                "validation",
                "test",
            ]
        )
        .to_string()
    )

    print(
        "\nLow-risk rows marked for model fitting:",
        int(
            assignment_df[
                "used_for_model_fit"
            ].sum()
        ),
    )

    print("\nUser overlap")
    print(
        "Fit-validation:",
        len(fit_validation_overlap),
    )
    print(
        "Fit-test:",
        len(fit_test_overlap),
    )
    print(
        "Validation-test:",
        len(validation_test_overlap),
    )

    print(
        "\nAssignments:",
        ASSIGNMENT_PATH.relative_to(
            PROJECT_ROOT
        ),
    )

    print(
        "Metadata:",
        METADATA_PATH.relative_to(
            PROJECT_ROOT
        ),
    )


if __name__ == "__main__":
    main()
