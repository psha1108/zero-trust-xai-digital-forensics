"""Persistence and integrity metadata for operational K-Means."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
from typing import Any, Final

import joblib
import numpy as np
import pandas as pd
import sklearn

from ml.clustering.train_operational_model import (
    DEFAULT_DATASET_PATH,
    DEFAULT_SPLIT_PATH,
    SELECTED_K,
    fit_operational_kmeans,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_ARTIFACT_PATH = (
    PROJECT_ROOT
    / "model_artifacts"
    / "operational"
    / "kmeans_behavioral_bundle.joblib"
)

DEFAULT_METADATA_PATH = (
    PROJECT_ROOT
    / "model_artifacts"
    / "operational"
    / "kmeans_behavioral_metadata.json"
)

SELECTION_REPORT_PATH = (
    PROJECT_ROOT
    / "results"
    / "metrics"
    / "operational_kmeans_selection.json"
)

EXPECTED_SELECTION_REPORT_SHA256: Final[str] = (
    "11be6247fa0fba344eafad08c5ad4aff65e4bf4463dc62743e719b3314b447a6"
)

# Raw artifact SHA-256 remains byte-for-byte exact. The semantic
# fingerprint normalizes insignificant floating-point implementation
# noise so equivalent fitted models retain one semantic identity.
FINGERPRINT_FLOAT_DECIMALS: Final[int] = 12


def sha256_file(
    path: Path,
) -> str:
    """Return lowercase SHA-256 for one file."""

    path = Path(path)

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def _canonical_json_bytes(
    value: Any,
) -> bytes:
    """Serialize a JSON-safe value deterministically."""

    text = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )

    return text.encode("utf-8")


def _normalized_float_string(
    value: float,
) -> str:
    """Return one stable decimal value for semantic fingerprinting."""

    numeric = float(value)

    if not np.isfinite(numeric):
        raise ValueError(
            "Semantic fingerprint values must be finite."
        )

    rounded = float(
        np.round(
            numeric,
            decimals=FINGERPRINT_FLOAT_DECIMALS,
        )
    )

    # Give positive and negative zero one semantic identity.
    if rounded == 0.0:
        rounded = 0.0

    return (
        f"{rounded:.{FINGERPRINT_FLOAT_DECIMALS}f}"
    )


def _normalized_float_list(
    values: np.ndarray,
) -> list[str]:
    """Normalize one floating-point vector for semantic hashing."""

    array = np.asarray(
        values,
        dtype=np.float64,
    )

    return [
        _normalized_float_string(
            value
        )
        for value in array.ravel()
    ]


def _normalized_float_matrix(
    values: np.ndarray,
) -> list[list[str]]:
    """Normalize one floating-point matrix for semantic hashing."""

    array = np.asarray(
        values,
        dtype=np.float64,
    )

    if array.ndim != 2:
        raise ValueError(
            "Expected a two-dimensional floating-point matrix."
        )

    return [
        [
            _normalized_float_string(
                value
            )
            for value in row
        ]
        for row in array
    ]


def _model_fingerprint_payload(
    bundle: dict[str, Any],
) -> dict[str, Any]:
    """Build semantic identity payload for the fitted K-Means model."""

    preprocessor = bundle[
        "preprocessor"
    ]

    model = bundle[
        "model"
    ]

    role_encoder = (
        preprocessor
        .named_transformers_["role"]
    )

    numeric_scaler = (
        preprocessor
        .named_transformers_["numeric"]
    )

    role_categories = [
        [
            str(value)
            for value in category_set
        ]
        for category_set in role_encoder.categories_
    ]

    mapping = {
        str(int(native_id)): int(
            canonical_id
        )
        for native_id, canonical_id in sorted(
            bundle[
                "native_to_canonical_cluster_id"
            ].items()
        )
    }

    canonical_names = {
        str(int(cluster_id)): str(name)
        for cluster_id, name in sorted(
            bundle[
                "canonical_archetype_names"
            ].items()
        )
    }

    payload = {
        "fingerprint_schema_version": 2,
        "float_decimal_places": FINGERPRINT_FLOAT_DECIMALS,
        "artifact_schema_version": int(
            bundle[
                "artifact_schema_version"
            ]
        ),
        "model_name": str(
            bundle["model_name"]
        ),
        "selected_k": int(
            bundle["selected_k"]
        ),
        "source_features": list(
            bundle["source_features"]
        ),
        "transformed_features": list(
            bundle["transformed_features"]
        ),
        "canonical_archetype_names": (
            canonical_names
        ),
        "native_to_canonical_cluster_id": (
            mapping
        ),
        "archetype_score_features": list(
            bundle[
                "archetype_score_features"
            ]
        ),
        "preprocessor": {
            "role_categories": role_categories,
            "numeric_mean_quantized": (
                _normalized_float_list(
                    numeric_scaler.mean_
                )
            ),
            "numeric_scale_quantized": (
                _normalized_float_list(
                    numeric_scaler.scale_
                )
            ),
            "numeric_var_quantized": (
                _normalized_float_list(
                    numeric_scaler.var_
                )
            ),
        },
        "kmeans": {
            "n_clusters": int(
                model.n_clusters
            ),
            "random_state": int(
                model.random_state
            ),
            "n_init": int(
                model.n_init
            ),
            "algorithm": str(
                model.algorithm
            ),
            "cluster_centers_quantized": (
                _normalized_float_matrix(
                    model.cluster_centers_
                )
            ),
            "inertia_quantized": (
                _normalized_float_string(
                    model.inertia_
                )
            ),
            "n_iter": int(
                model.n_iter_
            ),
        },
    }

    return payload


def compute_model_fingerprint(
    bundle: dict[str, Any],
) -> str:
    """Return deterministic semantic SHA-256 for a fitted bundle."""

    payload = _model_fingerprint_payload(
        bundle
    )

    return hashlib.sha256(
        _canonical_json_bytes(
            payload
        )
    ).hexdigest()


def compute_metadata_fingerprint(
    metadata: dict[str, Any],
) -> str:
    """
    Hash persisted metadata while excluding its own fingerprint field.
    """

    payload = dict(metadata)

    payload.pop(
        "metadata_fingerprint_sha256",
        None,
    )

    return hashlib.sha256(
        _canonical_json_bytes(
            payload
        )
    ).hexdigest()


def _load_and_verify_selection_report() -> dict[str, Any]:
    """Load the frozen development-selection evidence."""

    if not SELECTION_REPORT_PATH.is_file():
        raise FileNotFoundError(
            "Frozen K-Means selection report is missing: "
            f"{SELECTION_REPORT_PATH}"
        )

    actual_hash = sha256_file(
        SELECTION_REPORT_PATH
    )

    if (
        actual_hash
        != EXPECTED_SELECTION_REPORT_SHA256
    ):
        raise ValueError(
            "Frozen K-Means selection report SHA-256 changed. "
            f"Expected {EXPECTED_SELECTION_REPORT_SHA256}, "
            f"got {actual_hash}."
        )

    report = json.loads(
        SELECTION_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )

    if int(
        report["selected_k"]
    ) != SELECTED_K:
        raise ValueError(
            "Selection report does not contain frozen K=2."
        )

    if int(
        report[
            "test_rows_evaluated"
        ]
    ) != 0:
        raise ValueError(
            "Selection report indicates final-test evaluation."
        )

    if bool(
        report[
            "test_partition_used_for_selection"
        ]
    ):
        raise ValueError(
            "Selection report used final-test partition."
        )

    return report


def load_operational_kmeans_bundle(
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
) -> dict[str, Any]:
    """Load one persisted operational K-Means bundle."""

    artifact_path = Path(
        artifact_path
    )

    bundle = joblib.load(
        artifact_path
    )

    if not isinstance(
        bundle,
        dict,
    ):
        raise TypeError(
            "Operational K-Means artifact must contain a dictionary."
        )

    if int(
        bundle.get(
            "selected_k",
            -1,
        )
    ) != SELECTED_K:
        raise ValueError(
            "Persisted operational K-Means artifact is not K=2."
        )

    stored_fingerprint = bundle.get(
        "model_fingerprint_sha256"
    )

    if not isinstance(
        stored_fingerprint,
        str,
    ):
        raise ValueError(
            "Persisted bundle is missing model fingerprint."
        )

    actual_fingerprint = (
        compute_model_fingerprint(
            bundle
        )
    )

    if (
        actual_fingerprint
        != stored_fingerprint
    ):
        raise ValueError(
            "Persisted K-Means semantic fingerprint mismatch."
        )

    return bundle


def persist_operational_kmeans(
    *,
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
    metadata_path: Path = DEFAULT_METADATA_PATH,
    dataset_path: Path = DEFAULT_DATASET_PATH,
    split_path: Path = DEFAULT_SPLIT_PATH,
) -> dict[str, Any]:
    """
    Fit and persist the frozen final development K-Means artifact.

    This function performs no held-out final-test evaluation.
    """

    artifact_path = Path(
        artifact_path
    )

    metadata_path = Path(
        metadata_path
    )

    dataset_path = Path(
        dataset_path
    )

    split_path = Path(
        split_path
    )

    selection_report = (
        _load_and_verify_selection_report()
    )

    if (
        sha256_file(dataset_path)
        != selection_report[
            "dataset_sha256"
        ]
    ):
        raise ValueError(
            "Operational dataset SHA-256 differs from "
            "the frozen K-selection evidence."
        )

    if (
        sha256_file(split_path)
        != selection_report[
            "split_assignments_sha256"
        ]
    ):
        raise ValueError(
            "Operational split SHA-256 differs from "
            "the frozen K-selection evidence."
        )

    bundle, trainer_metadata = (
        fit_operational_kmeans(
            dataset_path=dataset_path,
            split_path=split_path,
        )
    )

    if (
        trainer_metadata[
            "test_rows_used_for_training"
        ]
        != 0
    ):
        raise ValueError(
            "Final-test rows entered model training."
        )

    model_fingerprint = (
        compute_model_fingerprint(
            bundle
        )
    )

    bundle[
        "model_fingerprint_sha256"
    ] = model_fingerprint

    artifact_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        bundle,
        artifact_path,
        compress=3,
    )

    artifact_sha256 = sha256_file(
        artifact_path
    )

    metadata: dict[str, Any] = dict(
        trainer_metadata
    )

    metadata.update(
        {
            "artifact_schema_version": int(
                bundle[
                    "artifact_schema_version"
                ]
            ),
            "artifact_filename": (
                artifact_path.name
            ),
            "artifact_sha256": (
                artifact_sha256
            ),
            "model_fingerprint_sha256": (
                model_fingerprint
            ),
            "selection_report_filename": (
                SELECTION_REPORT_PATH.name
            ),
            "selection_report_sha256": (
                EXPECTED_SELECTION_REPORT_SHA256
            ),
            "selection_selected_k": int(
                selection_report[
                    "selected_k"
                ]
            ),
            "dataset_filename": (
                dataset_path.name
            ),
            "dataset_sha256": (
                sha256_file(
                    dataset_path
                )
            ),
            "split_assignments_filename": (
                split_path.name
            ),
            "split_assignments_sha256": (
                sha256_file(
                    split_path
                )
            ),
            "software_versions": {
                "python": (
                    platform.python_version()
                ),
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scikit_learn": (
                    sklearn.__version__
                ),
                "joblib": (
                    joblib.__version__
                ),
            },
        }
    )

    metadata[
        "metadata_fingerprint_sha256"
    ] = compute_metadata_fingerprint(
        metadata
    )

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    verified_bundle = (
        load_operational_kmeans_bundle(
            artifact_path
        )
    )

    if (
        verified_bundle[
            "model_fingerprint_sha256"
        ]
        != model_fingerprint
    ):
        raise ValueError(
            "Persisted K-Means bundle verification failed."
        )

    return {
        "artifact_path": str(
            artifact_path
        ),
        "metadata_path": str(
            metadata_path
        ),
        "artifact_sha256": (
            artifact_sha256
        ),
        "model_fingerprint_sha256": (
            model_fingerprint
        ),
        "metadata_fingerprint_sha256": (
            metadata[
                "metadata_fingerprint_sha256"
            ]
        ),
        "selected_k": SELECTED_K,
        "training_rows": int(
            metadata[
                "training_rows"
            ]
        ),
        "training_users": int(
            metadata[
                "training_users"
            ]
        ),
        "test_rows_evaluated": 0,
    }


def main() -> None:
    """Persist the official operational K-Means artifact."""

    result = persist_operational_kmeans()

    print(
        "Operational K-Means artifact persisted."
    )

    print(
        "Artifact:",
        result[
            "artifact_path"
        ],
    )

    print(
        "Metadata:",
        result[
            "metadata_path"
        ],
    )

    print(
        "Selected K:",
        result[
            "selected_k"
        ],
    )

    print(
        "Training rows:",
        result[
            "training_rows"
        ],
    )

    print(
        "Training users:",
        result[
            "training_users"
        ],
    )

    print(
        "Artifact SHA256:",
        result[
            "artifact_sha256"
        ],
    )

    print(
        "Model fingerprint:",
        result[
            "model_fingerprint_sha256"
        ],
    )

    print(
        "Metadata fingerprint:",
        result[
            "metadata_fingerprint_sha256"
        ],
    )

    print(
        "Final-test rows evaluated:",
        result[
            "test_rows_evaluated"
        ],
    )


if __name__ == "__main__":
    main()
