"""Stable semantic fingerprinting for operational Random Forest artifacts."""

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

    digest.update(
        name.encode("utf-8")
    )
    digest.update(b"\0")

    digest.update(
        value.encode("utf-8")
    )
    digest.update(b"\0")


def _update_numeric_array(
    digest: Any,
    name: str,
    values,
) -> None:
    """Add a named numeric array to a canonical digest."""

    array = np.ascontiguousarray(
        values
    )

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
        array.tobytes(
            order="C"
        )
    )


def calculate_random_forest_semantic_fingerprint(
    artifact_bundle: dict,
) -> str:
    """Fingerprint the frozen Random Forest model and feature contract."""

    required_fields = {
        "artifact_schema_version",
        "model_name",
        "model_type",
        "selected_candidate_id",
        "source_feature_columns",
        "transformed_feature_columns",
        "transformed_source_feature_mapping",
        "role_categories",
        "class_order",
        "model_parameters",
        "model",
    }

    missing_fields = (
        required_fields
        -
        set(artifact_bundle)
    )

    if missing_fields:
        raise ValueError(
            "Random Forest fingerprint input is missing fields: "
            f"{sorted(missing_fields)}"
        )

    digest = hashlib.sha256()

    for field in [
        "artifact_schema_version",
        "model_name",
        "model_type",
        "selected_candidate_id",
    ]:
        _update_text(
            digest,
            field,
            str(
                artifact_bundle[
                    field
                ]
            ),
        )

    for field in [
        "source_feature_columns",
        "transformed_feature_columns",
        "transformed_source_feature_mapping",
        "role_categories",
        "class_order",
    ]:
        _update_text(
            digest,
            field,
            json.dumps(
                artifact_bundle[
                    field
                ],
                sort_keys=True,
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

    model = artifact_bundle[
        "model"
    ]

    actual_class_order = (
        np.asarray(
            model.classes_
        )
        .astype(str)
        .tolist()
    )

    if (
        actual_class_order
        != artifact_bundle[
            "class_order"
        ]
    ):
        raise ValueError(
            "Random Forest stored class order does not "
            "match model.classes_."
        )

    _update_text(
        digest,
        "model.classes",
        json.dumps(
            actual_class_order,
            separators=(",", ":"),
        ),
    )

    _update_numeric_array(
        digest,
        "model.n_features_in",
        np.asarray(
            [
                model.n_features_in_
            ],
            dtype=np.int64,
        ),
    )

    _update_numeric_array(
        digest,
        "model.n_outputs",
        np.asarray(
            [
                model.n_outputs_
            ],
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
                getattr(
                    tree,
                    attribute,
                ),
            )

    return digest.hexdigest()


METADATA_SEMANTIC_FIELDS = (
    "metadata_schema_version",
    "model_name",
    "model_type",
    "artifact_filename",
    "semantic_fingerprint",
    "reproducibility_definition",
    "dataset_filename",
    "dataset_canonical_sha256",
    "assignment_filename",
    "assignment_canonical_sha256",
    "selection_filename",
    "selection_canonical_sha256",
    "training_scope",
    "development_rows",
    "development_users",
    "development_label_counts",
    "source_feature_count",
    "transformed_feature_count",
    "source_feature_columns",
    "transformed_feature_columns",
    "transformed_source_feature_mapping",
    "role_categories",
    "selected_candidate_id",
    "model_parameters",
    "class_order",
    "class_to_index",
    "report_label_order",
)


def calculate_random_forest_metadata_semantic_fingerprint(
    metadata: dict,
) -> str:
    """Fingerprint the stable Random Forest metadata contract.

    Artifact byte checksums and software versions are intentionally
    excluded because they are provenance information rather than
    semantic model/feature/class identity.
    """

    if not isinstance(
        metadata,
        dict,
    ):
        raise TypeError(
            "Random Forest metadata must be a dictionary."
        )

    missing_fields = (
        set(METADATA_SEMANTIC_FIELDS)
        -
        set(metadata)
    )

    if missing_fields:
        raise ValueError(
            "Random Forest metadata fingerprint input "
            "is missing fields: "
            f"{sorted(missing_fields)}"
        )

    semantic_metadata = {
        field: metadata[field]
        for field in METADATA_SEMANTIC_FIELDS
    }

    canonical_json = json.dumps(
        semantic_metadata,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()
