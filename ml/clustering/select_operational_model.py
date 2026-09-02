"""Reproducible development selection for operational K-Means."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.clustering.preprocessing import (
    EXPECTED_TRANSFORMED_FEATURE_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    build_kmeans_preprocessor,
    get_transformed_feature_names,
    select_kmeans_features,
    transform_kmeans_features,
)
from ml.clustering.selection import (
    CANDIDATE_K_VALUES,
    KMEANS_ALGORITHM,
    KMEANS_N_INIT,
    KMEANS_RANDOM_STATE,
    evaluate_kmeans_candidate,
    select_best_k,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "ml_training_dataset.csv"
)

DEFAULT_SPLIT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "operational"
    / "isolation_forest_split_assignments.csv"
)

DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT
    / "results"
    / "metrics"
    / "operational_kmeans_selection.json"
)


DEVELOPMENT_ARCHETYPES = {
    "0": "Elevated Behavioral Activity",
    "1": "Routine Behavioral Activity",
}

ARCHETYPE_SEMANTICS = (
    "behavioral context only; cluster IDs are not "
    "risk classes or access-control decisions"
)


def _sha256_file(
    path: Path,
) -> str:
    """Return the SHA-256 digest of one file."""

    digest = hashlib.sha256()

    with path.open("rb") as file_handle:
        for chunk in iter(
            lambda: file_handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def _load_development_partitions(
    *,
    dataset_path: Path,
    split_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, int, int, int]:
    """
    Load only the fit and validation partitions used for K selection.

    The held-out final test partition is deliberately not returned.
    """

    dataset = pd.read_csv(dataset_path)
    assignments = pd.read_csv(split_path)

    if len(dataset) != 845:
        raise ValueError(
            f"Unexpected operational dataset rows: {len(dataset)}"
        )

    if len(assignments) != 845:
        raise ValueError(
            f"Unexpected split assignment rows: {len(assignments)}"
        )

    required_split_columns = {
        "source_row_index",
        "user_id",
        "partition",
    }

    missing_split_columns = sorted(
        required_split_columns
        - set(assignments.columns)
    )

    if missing_split_columns:
        raise ValueError(
            "Split assignments are missing required columns: "
            + ", ".join(missing_split_columns)
        )

    expected_indices = np.arange(
        len(dataset),
        dtype=np.int64,
    )

    actual_indices = pd.to_numeric(
        assignments["source_row_index"],
        errors="raise",
    ).to_numpy(dtype=np.int64)

    if not np.array_equal(
        expected_indices,
        actual_indices,
    ):
        raise ValueError(
            "Dataset rows do not align with source_row_index."
        )

    if not dataset[
        "user_id"
    ].astype(str).equals(
        assignments["user_id"].astype(str)
    ):
        raise ValueError(
            "Dataset and split user_id rows do not align."
        )

    fit_mask = assignments[
        "partition"
    ].eq("fit")

    validation_mask = assignments[
        "partition"
    ].eq("validation")

    fit_df = dataset.loc[
        fit_mask
    ].copy()

    validation_df = dataset.loc[
        validation_mask
    ].copy()

    if len(fit_df) != 554:
        raise ValueError(
            f"Unexpected fit rows: {len(fit_df)}"
        )

    if len(validation_df) != 138:
        raise ValueError(
            "Unexpected validation rows: "
            f"{len(validation_df)}"
        )

    fit_users = set(
        fit_df["user_id"].astype(str)
    )

    validation_users = set(
        validation_df["user_id"].astype(str)
    )

    if len(fit_users) != 32:
        raise ValueError(
            f"Unexpected fit users: {len(fit_users)}"
        )

    if len(validation_users) != 8:
        raise ValueError(
            "Unexpected validation users: "
            f"{len(validation_users)}"
        )

    overlap = fit_users & validation_users

    if overlap:
        raise ValueError(
            "User leakage detected between fit and validation."
        )

    return (
        fit_df,
        validation_df,
        len(fit_users),
        len(validation_users),
        len(overlap),
    )


def run_development_selection(
    *,
    dataset_path: Path = DEFAULT_DATASET_PATH,
    split_path: Path = DEFAULT_SPLIT_PATH,
) -> dict[str, Any]:
    """
    Run the frozen K=2..8 development-only selection procedure.

    Only fit and validation partitions participate in model selection.
    The final test partition is not transformed, predicted, or scored.
    """

    dataset_path = Path(dataset_path)
    split_path = Path(split_path)

    (
        fit_df,
        validation_df,
        fit_user_count,
        validation_user_count,
        overlap_count,
    ) = _load_development_partitions(
        dataset_path=dataset_path,
        split_path=split_path,
    )

    preprocessor = build_kmeans_preprocessor()

    fit_features = select_kmeans_features(
        fit_df
    )

    fit_matrix = np.asarray(
        preprocessor.fit_transform(
            fit_features
        ),
        dtype=np.float64,
    )

    validation_matrix = transform_kmeans_features(
        preprocessor,
        validation_df,
    )

    transformed_feature_names = (
        get_transformed_feature_names(
            preprocessor
        )
    )

    if fit_matrix.shape != (554, 18):
        raise ValueError(
            "Unexpected fit transformed shape: "
            f"{fit_matrix.shape}"
        )

    if validation_matrix.shape != (138, 18):
        raise ValueError(
            "Unexpected validation transformed shape: "
            f"{validation_matrix.shape}"
        )

    candidates = [
        evaluate_kmeans_candidate(
            k=k,
            fit_matrix=fit_matrix,
            validation_matrix=validation_matrix,
        )
        for k in CANDIDATE_K_VALUES
    ]

    selected = select_best_k(
        candidates
    )

    return {
        "fit_rows": int(len(fit_df)),
        "validation_rows": int(
            len(validation_df)
        ),
        "fit_users": int(
            fit_user_count
        ),
        "validation_users": int(
            validation_user_count
        ),
        "user_overlap": int(
            overlap_count
        ),
        "test_rows_evaluated": 0,
        "candidate_k_values": list(
            CANDIDATE_K_VALUES
        ),
        "source_feature_count": len(
            MODEL_FEATURE_COLUMNS
        ),
        "transformed_feature_count": len(
            EXPECTED_TRANSFORMED_FEATURE_COLUMNS
        ),
        "source_features": list(
            MODEL_FEATURE_COLUMNS
        ),
        "transformed_features": list(
            transformed_feature_names
        ),
        "candidates": candidates,
        "selected_k": int(
            selected["k"]
        ),
        "selected_candidate": selected,
    }


def build_selection_report(
    development: dict[str, Any],
    *,
    dataset_path: Path = DEFAULT_DATASET_PATH,
    split_path: Path = DEFAULT_SPLIT_PATH,
) -> dict[str, Any]:
    """Build the persisted development model-selection evidence."""

    selected_k = int(
        development["selected_k"]
    )

    if selected_k != 2:
        raise ValueError(
            "Frozen operational K-Means development selection "
            f"expected K=2, got K={selected_k}."
        )

    return {
        "report_schema_version": 1,
        "model_name": (
            "operational_kmeans_behavioral_clustering"
        ),
        "model_type": "KMeans",
        "task": (
            "unsupervised_behavioral_clustering"
        ),
        "dataset": Path(
            dataset_path
        ).name,
        "dataset_sha256": _sha256_file(
            Path(dataset_path)
        ),
        "split_assignments": Path(
            split_path
        ).name,
        "split_assignments_sha256": _sha256_file(
            Path(split_path)
        ),
        "source_feature_count": development[
            "source_feature_count"
        ],
        "transformed_feature_count": development[
            "transformed_feature_count"
        ],
        "source_features": development[
            "source_features"
        ],
        "transformed_features": development[
            "transformed_features"
        ],
        "candidate_k_values": development[
            "candidate_k_values"
        ],
        "kmeans_parameters": {
            "random_state": KMEANS_RANDOM_STATE,
            "n_init": KMEANS_N_INIT,
            "algorithm": KMEANS_ALGORITHM,
        },
        "development_partitions": {
            "fit": {
                "rows": development[
                    "fit_rows"
                ],
                "users": development[
                    "fit_users"
                ],
            },
            "validation": {
                "rows": development[
                    "validation_rows"
                ],
                "users": development[
                    "validation_users"
                ],
            },
            "user_overlap": development[
                "user_overlap"
            ],
        },
        "selection_metric": (
            "validation_silhouette_score"
        ),
        "selection_tie_breakers": [
            "lower_validation_davies_bouldin_index",
            "higher_validation_calinski_harabasz_score",
            "smaller_k",
        ],
        "selected_k": selected_k,
        "selected_candidate": development[
            "selected_candidate"
        ],
        "candidates": development[
            "candidates"
        ],
        "development_archetypes": dict(
            DEVELOPMENT_ARCHETYPES
        ),
        "archetype_semantics": (
            ARCHETYPE_SEMANTICS
        ),
        "risk_label_used_for_training": False,
        "risk_label_used_for_selection": False,
        "scenario_type_used_for_training": False,
        "scenario_type_used_for_selection": False,
        "test_partition_used_for_selection": False,
        "test_rows_evaluated": 0,
    }


def write_selection_report(
    *,
    dataset_path: Path = DEFAULT_DATASET_PATH,
    split_path: Path = DEFAULT_SPLIT_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> dict[str, Any]:
    """Run development selection and persist its JSON evidence."""

    development = run_development_selection(
        dataset_path=dataset_path,
        split_path=split_path,
    )

    report = build_selection_report(
        development,
        dataset_path=dataset_path,
        split_path=split_path,
    )

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return report


def main() -> None:
    """CLI entry point for reproducible development K selection."""

    parser = argparse.ArgumentParser(
        description=(
            "Run development-only operational "
            "K-Means model selection."
        )
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
    )

    parser.add_argument(
        "--split",
        type=Path,
        default=DEFAULT_SPLIT_PATH,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    args = parser.parse_args()

    report = write_selection_report(
        dataset_path=args.dataset,
        split_path=args.split,
        output_path=args.output,
    )

    selected = report[
        "selected_candidate"
    ]

    validation = selected[
        "validation_metrics"
    ]

    print(
        "Operational K-Means development selection completed."
    )

    print(
        "Selected K:",
        report["selected_k"],
    )

    print(
        "Validation silhouette:",
        f"{validation['silhouette_score']:.12f}",
    )

    print(
        "Validation Davies-Bouldin:",
        f"{validation['davies_bouldin_index']:.12f}",
    )

    print(
        "Validation Calinski-Harabasz:",
        f"{validation['calinski_harabasz_score']:.12f}",
    )

    print(
        "Validation cluster sizes:",
        validation["cluster_sizes"],
    )

    print(
        "Final-test rows evaluated:",
        report["test_rows_evaluated"],
    )

    print(
        "Report:",
        args.output,
    )


if __name__ == "__main__":
    main()
