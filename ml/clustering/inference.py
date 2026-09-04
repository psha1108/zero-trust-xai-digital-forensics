"""Inference API for frozen operational K-Means clustering."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.clustering.persist_operational_model import (
    DEFAULT_ARTIFACT_PATH,
    load_operational_kmeans_bundle,
)
from ml.clustering.preprocessing import (
    EXPECTED_TRANSFORMED_FEATURE_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    select_kmeans_features,
)
from ml.clustering.train_operational_model import (
    CANONICAL_ARCHETYPE_NAMES,
    SELECTED_K,
)


def _resolve_bundle(
    bundle_path: Path | None,
) -> dict[str, Any]:
    """Load and validate the frozen operational K-Means bundle."""

    path = (
        DEFAULT_ARTIFACT_PATH
        if bundle_path is None
        else Path(bundle_path)
    )

    bundle = load_operational_kmeans_bundle(
        path
    )

    if int(
        bundle.get(
            "selected_k",
            -1,
        )
    ) != SELECTED_K:
        raise ValueError(
            "Operational K-Means bundle does not use frozen K=2."
        )

    if list(
        bundle.get(
            "source_features",
            [],
        )
    ) != list(
        MODEL_FEATURE_COLUMNS
    ):
        raise ValueError(
            "Operational K-Means bundle source-feature "
            "contract does not match the frozen 14 features."
        )

    if list(
        bundle.get(
            "transformed_features",
            [],
        )
    ) != list(
        EXPECTED_TRANSFORMED_FEATURE_COLUMNS
    ):
        raise ValueError(
            "Operational K-Means bundle transformed-feature "
            "contract does not match the frozen 18 features."
        )

    mapping = bundle.get(
        "native_to_canonical_cluster_id"
    )

    if not isinstance(
        mapping,
        dict,
    ):
        raise ValueError(
            "Operational K-Means bundle is missing "
            "native-to-canonical mapping."
        )

    normalized_mapping = {
        int(native_id): int(
            canonical_id
        )
        for native_id, canonical_id in (
            mapping.items()
        )
    }

    if set(
        normalized_mapping.keys()
    ) != {
        0,
        1,
    }:
        raise ValueError(
            "Operational K-Means native cluster IDs are invalid."
        )

    if set(
        normalized_mapping.values()
    ) != {
        0,
        1,
    }:
        raise ValueError(
            "Operational K-Means canonical cluster IDs are invalid."
        )

    names = bundle.get(
        "canonical_archetype_names"
    )

    if names != CANONICAL_ARCHETYPE_NAMES:
        raise ValueError(
            "Operational K-Means archetype-name contract changed."
        )

    return bundle


def _records_to_frame(
    records: Sequence[
        Mapping[str, Any]
    ],
) -> pd.DataFrame:
    """Build and validate an ordered operational inference frame."""

    if len(records) == 0:
        raise ValueError(
            "K-Means inference requires at least one record; "
            "the input batch cannot be empty."
        )

    normalized_records: list[
        dict[str, Any]
    ] = []

    for index, record in enumerate(
        records
    ):
        if not isinstance(
            record,
            Mapping,
        ):
            raise ValueError(
                "Each K-Means inference record must be "
                f"a mapping; record {index} is invalid."
            )

        missing = [
            feature
            for feature in MODEL_FEATURE_COLUMNS
            if feature not in record
        ]

        if missing:
            raise ValueError(
                "K-Means inference record is missing required "
                "operational features: "
                + ", ".join(
                    missing
                )
            )

        normalized_records.append(
            {
                feature: record[
                    feature
                ]
                for feature in MODEL_FEATURE_COLUMNS
            }
        )

    frame = pd.DataFrame(
        normalized_records,
        columns=MODEL_FEATURE_COLUMNS,
    )

    return select_kmeans_features(
        frame
    )


def cluster_operational_records(
    records: Sequence[
        Mapping[str, Any]
    ],
    *,
    bundle_path: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Assign operational records to canonical behavioral archetypes.

    Cluster IDs provide behavioral context only. This function does not
    produce risk classes or access-control policy decisions.
    """

    frame = _records_to_frame(
        records
    )

    bundle = _resolve_bundle(
        bundle_path
    )

    transformed = np.asarray(
        bundle[
            "preprocessor"
        ].transform(
            frame
        ),
        dtype=np.float64,
    )

    expected_shape = (
        len(frame),
        len(
            EXPECTED_TRANSFORMED_FEATURE_COLUMNS
        ),
    )

    if transformed.shape != expected_shape:
        raise ValueError(
            "Unexpected operational K-Means transformed shape: "
            f"{transformed.shape}; expected {expected_shape}."
        )

    if not np.isfinite(
        transformed
    ).all():
        raise ValueError(
            "Operational K-Means transformed inference "
            "matrix contains non-finite values."
        )

    native_labels = np.asarray(
        bundle[
            "model"
        ].predict(
            transformed
        ),
        dtype=np.int64,
    )

    if native_labels.shape != (
        len(frame),
    ):
        raise ValueError(
            "Operational K-Means prediction count does not "
            "match input record count."
        )

    mapping = {
        int(native_id): int(
            canonical_id
        )
        for native_id, canonical_id in (
            bundle[
                "native_to_canonical_cluster_id"
            ].items()
        )
    }

    archetype_names = {
        int(cluster_id): str(
            name
        )
        for cluster_id, name in (
            bundle[
                "canonical_archetype_names"
            ].items()
        )
    }

    results: list[
        dict[str, Any]
    ] = []

    for native_label in native_labels:
        native_cluster_id = int(
            native_label
        )

        if native_cluster_id not in mapping:
            raise ValueError(
                "Operational K-Means produced an unknown "
                f"native cluster ID: {native_cluster_id}."
            )

        canonical_cluster_id = int(
            mapping[
                native_cluster_id
            ]
        )

        if (
            canonical_cluster_id
            not in archetype_names
        ):
            raise ValueError(
                "Operational K-Means canonical cluster "
                "does not have an archetype name."
            )

        results.append(
            {
                "cluster_id": (
                    canonical_cluster_id
                ),
                "archetype_name": (
                    archetype_names[
                        canonical_cluster_id
                    ]
                ),
            }
        )

    return results


def cluster_operational_record(
    record: Mapping[str, Any],
    *,
    bundle_path: Path | None = None,
) -> dict[str, Any]:
    """Assign one operational record to a behavioral archetype."""

    results = cluster_operational_records(
        [
            record,
        ],
        bundle_path=bundle_path,
    )

    return results[0]
