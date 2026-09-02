"""Stable semantic fingerprinting for Isolation Forest artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np


def _update_text(
    digest: Any,
    name: str,
    value: str,
) -> None:
    """Add named text to a canonical digest."""

    digest.update(name.encode("utf-8"))
    digest.update(b"\0")
    digest.update(value.encode("utf-8"))
    digest.update(b"\0")


def _update_numeric_array(
    digest: Any,
    name: str,
    values,
) -> None:
    """Add a named numeric array to a canonical digest."""

    array = np.ascontiguousarray(values)

    _update_text(
        digest,
        f"{name}.dtype",
        str(array.dtype),
    )

    _update_text(
        digest,
        f"{name}.shape",
        json.dumps(
            list(array.shape),
            separators=(",", ":"),
        ),
    )

    digest.update(
        array.tobytes(order="C")
    )


def calculate_isolation_forest_semantic_fingerprint(
    artifact_bundle: dict,
) -> str:
    """Fingerprint model structure, schema and operating threshold."""

    digest = hashlib.sha256()

    _update_text(
        digest,
        "artifact_schema_version",
        str(
            artifact_bundle[
                "artifact_schema_version"
            ]
        ),
    )

    for field in [
        "model_name",
        "model_type",
        "score_definition",
        "score_direction",
    ]:
        _update_text(
            digest,
            field,
            str(artifact_bundle[field]),
        )

    for field in [
        "source_feature_columns",
        "transformed_feature_columns",
        "role_categories",
        "constant_low_risk_features",
    ]:
        _update_text(
            digest,
            field,
            json.dumps(
                artifact_bundle[field],
                separators=(",", ":"),
            ),
        )

    _update_text(
        digest,
        "model_parameters",
        json.dumps(
            artifact_bundle[
                "model_parameters"
            ],
            sort_keys=True,
            separators=(",", ":"),
        ),
    )

    _update_numeric_array(
        digest,
        "anomaly_threshold",
        np.asarray(
            [
                artifact_bundle[
                    "anomaly_threshold"
                ]
            ],
            dtype=np.float64,
        ),
    )

    model = artifact_bundle["model"]

    _update_numeric_array(
        digest,
        "model.offset",
        np.asarray(
            [model.offset_],
            dtype=np.float64,
        ),
    )

    _update_numeric_array(
        digest,
        "model.max_samples",
        np.asarray(
            [model.max_samples_],
            dtype=np.int64,
        ),
    )

    for estimator_number, feature_indices in enumerate(
        model.estimators_features_
    ):
        _update_numeric_array(
            digest,
            (
                "estimator_features."
                f"{estimator_number}"
            ),
            np.asarray(
                feature_indices,
                dtype=np.int64,
            ),
        )

    tree_attributes = [
        "children_left",
        "children_right",
        "feature",
        "threshold",
        "impurity",
        "n_node_samples",
        "weighted_n_node_samples",
        "value",
    ]

    for estimator_number, estimator in enumerate(
        model.estimators_
    ):
        tree = estimator.tree_

        for attribute in tree_attributes:
            _update_numeric_array(
                digest,
                (
                    f"tree.{estimator_number}."
                    f"{attribute}"
                ),
                getattr(tree, attribute),
            )

    return digest.hexdigest()
