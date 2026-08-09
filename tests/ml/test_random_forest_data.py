"""Tests for the Random Forest data and shared split contract."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ml.classification.data import (
    ASSIGNMENT_PATH,
    DATASET_PATH,
    EXPECTED_ASSIGNMENT_CANONICAL_SHA256,
    EXPECTED_DATASET_CANONICAL_SHA256,
    calculate_canonical_text_sha256,
    load_random_forest_selection_data,
)


def test_canonical_dataset_and_split_fingerprints() -> None:
    """The approved dataset and partition assignment must be stable."""

    assert (
        calculate_canonical_text_sha256(
            DATASET_PATH
        )
        ==
        EXPECTED_DATASET_CANONICAL_SHA256
    )

    assert (
        calculate_canonical_text_sha256(
            ASSIGNMENT_PATH
        )
        ==
        EXPECTED_ASSIGNMENT_CANONICAL_SHA256
    )


def test_canonical_checksum_normalizes_line_endings(
    tmp_path: Path,
) -> None:
    """LF and CRLF representations must have the same checksum."""

    lf_path = tmp_path / "lf.txt"
    crlf_path = tmp_path / "crlf.txt"

    lf_path.write_bytes(
        b"alpha\nbeta\ngamma\n"
    )

    crlf_path.write_bytes(
        b"alpha\r\nbeta\r\ngamma\r\n"
    )

    assert (
        calculate_canonical_text_sha256(
            lf_path
        )
        ==
        calculate_canonical_text_sha256(
            crlf_path
        )
    )


def test_selection_loader_returns_only_fit_and_validation() -> None:
    """Model selection must not receive final-test records."""

    fit_df, validation_df = (
        load_random_forest_selection_data()
    )

    assert len(fit_df) == 554
    assert len(validation_df) == 138

    assert fit_df[
        "partition"
    ].eq("fit").all()

    assert validation_df[
        "partition"
    ].eq("validation").all()

    assert "test" not in set(
        fit_df["partition"]
    )

    assert "test" not in set(
        validation_df["partition"]
    )


def test_supervised_fit_uses_all_fit_labels() -> None:
    """Random Forest must not use the Isolation Forest low-only marker."""

    fit_df, _ = (
        load_random_forest_selection_data()
    )

    assert fit_df[
        "risk_label"
    ].value_counts().to_dict() == {
        "low": 362,
        "medium": 129,
        "high": 63,
    }

    assert set(
        fit_df["risk_label"]
    ) == {
        "low",
        "medium",
        "high",
    }


def test_fit_validation_user_separation() -> None:
    """Fit and validation users must remain completely separate."""

    fit_df, validation_df = (
        load_random_forest_selection_data()
    )

    assert fit_df[
        "user_id"
    ].nunique() == 32

    assert validation_df[
        "user_id"
    ].nunique() == 8

    assert not (
        set(fit_df["user_id"])
        &
        set(validation_df["user_id"])
    )


def test_source_row_identity_is_preserved() -> None:
    """Returned records must retain their original source-row IDs."""

    source_df = pd.read_csv(
        DATASET_PATH
    )

    fit_df, validation_df = (
        load_random_forest_selection_data()
    )

    returned = pd.concat(
        [
            fit_df,
            validation_df,
        ]
    ).sort_values(
        "source_row_index"
    )

    for _, row in returned.iterrows():
        source_row = source_df.iloc[
            int(row["source_row_index"])
        ]

        assert row["user_id"] == source_row["user_id"]
        assert row["risk_label"] == source_row["risk_label"]
        assert row["scenario_type"] == source_row["scenario_type"]


def test_development_loader_combines_only_fit_and_validation() -> None:
    """Final training data must contain development records only."""

    from ml.classification.data import (
        load_random_forest_development_data,
    )

    development_df = (
        load_random_forest_development_data()
    )

    assert len(development_df) == 692

    assert development_df[
        "user_id"
    ].nunique() == 40

    assert set(
        development_df["partition"]
    ) == {
        "fit",
        "validation",
    }

    assert "test" not in set(
        development_df["partition"]
    )


def test_development_loader_target_distribution() -> None:
    """Combined development labels must match the frozen split."""

    from ml.classification.data import (
        load_random_forest_development_data,
    )

    development_df = (
        load_random_forest_development_data()
    )

    assert development_df[
        "risk_label"
    ].value_counts().to_dict() == {
        "low": 452,
        "medium": 162,
        "high": 78,
    }


def test_development_loader_preserves_source_identity() -> None:
    """Combined development rows must preserve original row IDs."""

    from ml.classification.data import (
        load_random_forest_development_data,
    )

    development_df = (
        load_random_forest_development_data()
    )

    assert development_df[
        "source_row_index"
    ].is_unique

    assert development_df[
        "source_row_index"
    ].is_monotonic_increasing

    assert len(
        set(
            development_df[
                "source_row_index"
            ]
        )
    ) == 692
