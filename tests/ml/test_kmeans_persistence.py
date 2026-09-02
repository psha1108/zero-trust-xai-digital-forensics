"""Tests for persisted operational K-Means artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pytest
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer

from ml.clustering.persist_operational_model import (
    EXPECTED_SELECTION_REPORT_SHA256,
    compute_metadata_fingerprint,
    compute_model_fingerprint,
    load_operational_kmeans_bundle,
    persist_operational_kmeans,
    sha256_file,
)
from ml.clustering.train_operational_model import (
    CANONICAL_ARCHETYPE_NAMES,
    fit_operational_kmeans,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def persisted_artifacts(
    tmp_path_factory: pytest.TempPathFactory,
):
    output_dir = tmp_path_factory.mktemp(
        "operational_kmeans_artifacts"
    )

    artifact_path = (
        output_dir
        / "kmeans_behavioral_bundle.joblib"
    )

    metadata_path = (
        output_dir
        / "kmeans_behavioral_metadata.json"
    )

    result = persist_operational_kmeans(
        artifact_path=artifact_path,
        metadata_path=metadata_path,
    )

    return {
        "result": result,
        "artifact_path": artifact_path,
        "metadata_path": metadata_path,
    }


def test_model_semantic_fingerprint_is_repeatable() -> None:
    first_bundle, _ = fit_operational_kmeans()
    second_bundle, _ = fit_operational_kmeans()

    first = compute_model_fingerprint(
        first_bundle
    )

    second = compute_model_fingerprint(
        second_bundle
    )

    assert first == second
    assert len(first) == 64

    int(first, 16)


def test_persistence_writes_joblib_and_metadata(
    persisted_artifacts,
) -> None:
    artifact_path = persisted_artifacts[
        "artifact_path"
    ]

    metadata_path = persisted_artifacts[
        "metadata_path"
    ]

    assert artifact_path.is_file()
    assert metadata_path.is_file()

    metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    assert metadata[
        "model_name"
    ] == "operational_kmeans_behavioral_clustering"

    assert metadata["selected_k"] == 2

    assert metadata[
        "training_partition"
    ] == "fit_plus_validation"

    assert metadata[
        "training_rows"
    ] == 692

    assert metadata[
        "training_users"
    ] == 40

    assert metadata[
        "test_rows_used_for_training"
    ] == 0

    assert metadata[
        "test_partition_used_for_training"
    ] is False


def test_persisted_bundle_loads_with_exact_contract(
    persisted_artifacts,
) -> None:
    artifact_path = persisted_artifacts[
        "artifact_path"
    ]

    metadata_path = persisted_artifacts[
        "metadata_path"
    ]

    bundle = load_operational_kmeans_bundle(
        artifact_path
    )

    metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    assert bundle[
        "artifact_schema_version"
    ] == 1

    assert bundle["selected_k"] == 2

    assert isinstance(
        bundle["preprocessor"],
        ColumnTransformer,
    )

    assert isinstance(
        bundle["model"],
        KMeans,
    )

    assert bundle["model"].n_clusters == 2

    assert bundle[
        "canonical_archetype_names"
    ] == CANONICAL_ARCHETYPE_NAMES

    assert set(
        bundle[
            "native_to_canonical_cluster_id"
        ].keys()
    ) == {
        0,
        1,
    }

    assert set(
        bundle[
            "native_to_canonical_cluster_id"
        ].values()
    ) == {
        0,
        1,
    }

    assert bundle[
        "model_fingerprint_sha256"
    ] == metadata[
        "model_fingerprint_sha256"
    ]

    assert (
        compute_model_fingerprint(bundle)
        == metadata[
            "model_fingerprint_sha256"
        ]
    )


def test_artifact_raw_sha_matches_metadata(
    persisted_artifacts,
) -> None:
    artifact_path = persisted_artifacts[
        "artifact_path"
    ]

    metadata_path = persisted_artifacts[
        "metadata_path"
    ]

    metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        sha256_file(artifact_path)
        == metadata[
            "artifact_sha256"
        ]
    )


def test_metadata_fingerprint_verifies(
    persisted_artifacts,
) -> None:
    metadata_path = persisted_artifacts[
        "metadata_path"
    ]

    metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    stored = metadata[
        "metadata_fingerprint_sha256"
    ]

    assert len(stored) == 64
    int(stored, 16)

    assert (
        compute_metadata_fingerprint(
            metadata
        )
        == stored
    )


def test_selection_provenance_and_unsupervised_contract(
    persisted_artifacts,
) -> None:
    metadata_path = persisted_artifacts[
        "metadata_path"
    ]

    metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    assert metadata[
        "selection_report_sha256"
    ] == EXPECTED_SELECTION_REPORT_SHA256

    assert metadata[
        "selection_selected_k"
    ] == 2

    assert metadata[
        "risk_label_used_for_training"
    ] is False

    assert metadata[
        "scenario_type_used_for_training"
    ] is False

    assert metadata[
        "user_id_used_for_training"
    ] is False

    assert metadata[
        "archetype_semantics"
    ] == (
        "behavioral context only; cluster IDs are not "
        "risk classes or access-control decisions"
    )

    assert metadata[
        "canonical_archetype_names"
    ] == {
        "0": "Elevated Behavioral Activity",
        "1": "Routine Behavioral Activity",
    }


def test_model_semantic_fingerprint_detects_material_change() -> None:
    bundle, _ = fit_operational_kmeans()

    original = compute_model_fingerprint(
        bundle
    )

    bundle[
        "model"
    ].cluster_centers_[0, 0] += 1e-6

    changed = compute_model_fingerprint(
        bundle
    )

    assert changed != original
