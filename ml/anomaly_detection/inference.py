"""Reusable inference functions for the operational Isolation Forest."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ml.anomaly_detection.fingerprinting import (
    calculate_isolation_forest_semantic_fingerprint,
)
from ml.anomaly_detection.preprocessing import (
    MODEL_FEATURE_COLUMNS,
    transform_operational_features,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_MODEL_PATH = (
    PROJECT_ROOT
    / "model_artifacts"
    / "operational"
    / "isolation_forest_bundle.joblib"
)

EXPECTED_ARTIFACT_SCHEMA_VERSION = 2

REQUIRED_ARTIFACT_FIELDS = {
    "artifact_schema_version",
    "model_name",
    "model_type",
    "preprocessor",
    "model",
    "anomaly_threshold",
    "semantic_fingerprint",
    "source_feature_columns",
    "transformed_feature_columns",
    "score_definition",
    "score_direction",
}


def validate_isolation_forest_bundle(
    artifact_bundle: dict[str, Any],
) -> None:
    """Validate the loaded Isolation Forest artifact contract."""

    if not isinstance(
        artifact_bundle,
        dict,
    ):
        raise TypeError(
            "Isolation Forest artifact must be a dictionary."
        )

    missing_fields = (
        REQUIRED_ARTIFACT_FIELDS
        -
        set(artifact_bundle)
    )

    if missing_fields:
        raise ValueError(
            "Isolation Forest artifact is missing fields: "
            f"{sorted(missing_fields)}"
        )

    if artifact_bundle[
        "artifact_schema_version"
    ] != EXPECTED_ARTIFACT_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported Isolation Forest artifact schema: "
            f"{artifact_bundle['artifact_schema_version']}"
        )

    if artifact_bundle[
        "model_name"
    ] != "operational_isolation_forest":
        raise ValueError(
            "Unexpected Isolation Forest model name."
        )

    if artifact_bundle[
        "model_type"
    ] != "IsolationForest":
        raise ValueError(
            "Unexpected Isolation Forest model type."
        )

    if artifact_bundle[
        "source_feature_columns"
    ] != list(MODEL_FEATURE_COLUMNS):
        raise ValueError(
            "Isolation Forest source-feature contract changed."
        )

    if artifact_bundle[
        "score_direction"
    ] != "higher_is_more_anomalous":
        raise ValueError(
            "Unexpected anomaly-score direction."
        )

    anomaly_threshold = float(
        artifact_bundle[
            "anomaly_threshold"
        ]
    )

    if not np.isfinite(
        anomaly_threshold
    ):
        raise ValueError(
            "Isolation Forest anomaly threshold is not finite."
        )

    model = artifact_bundle["model"]

    if not hasattr(
        model,
        "score_samples",
    ):
        raise ValueError(
            "Artifact model does not support score_samples()."
        )

    preprocessor = artifact_bundle[
        "preprocessor"
    ]

    if not hasattr(
        preprocessor,
        "transform",
    ):
        raise ValueError(
            "Artifact preprocessor does not support transform()."
        )

    calculated_fingerprint = (
        calculate_isolation_forest_semantic_fingerprint(
            artifact_bundle
        )
    )

    stored_fingerprint = artifact_bundle[
        "semantic_fingerprint"
    ]

    if (
        calculated_fingerprint
        !=
        stored_fingerprint
    ):
        raise ValueError(
            "Isolation Forest semantic fingerprint mismatch."
        )


def load_isolation_forest_bundle(
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> dict[str, Any]:
    """Load and validate the operational model artifact."""

    resolved_path = Path(
        model_path
    ).resolve()

    if not resolved_path.is_file():
        raise FileNotFoundError(
            "Isolation Forest artifact was not found: "
            f"{resolved_path}"
        )

    artifact_bundle = joblib.load(
        resolved_path
    )

    validate_isolation_forest_bundle(
        artifact_bundle
    )

    return artifact_bundle


def score_operational_records(
    records: pd.DataFrame,
    *,
    artifact_bundle: dict[str, Any] | None = None,
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> pd.DataFrame:
    """Score one or more operational behavioral records.

    The returned anomaly score is higher for more anomalous
    behavior. A record is anomalous when its score is greater
    than or equal to the saved operating threshold.
    """

    if not isinstance(
        records,
        pd.DataFrame,
    ):
        raise TypeError(
            "Operational records must be provided "
            "as a pandas DataFrame."
        )

    if records.empty:
        raise ValueError(
            "At least one operational record is required."
        )

    if artifact_bundle is None:
        artifact_bundle = (
            load_isolation_forest_bundle(
                model_path
            )
        )
    else:
        validate_isolation_forest_bundle(
            artifact_bundle
        )

    transformed_matrix = (
        transform_operational_features(
            artifact_bundle[
                "preprocessor"
            ],
            records,
        )
    )

    anomaly_scores = np.asarray(
        -artifact_bundle[
            "model"
        ].score_samples(
            transformed_matrix
        ),
        dtype=np.float64,
    )

    if anomaly_scores.shape != (
        len(records),
    ):
        raise RuntimeError(
            "Isolation Forest returned an unexpected "
            "number of anomaly scores."
        )

    if not np.isfinite(
        anomaly_scores
    ).all():
        raise RuntimeError(
            "Isolation Forest returned non-finite scores."
        )

    anomaly_threshold = float(
        artifact_bundle[
            "anomaly_threshold"
        ]
    )

    threshold_margins = (
        anomaly_scores
        -
        anomaly_threshold
    )

    predictions = (
        anomaly_scores
        >=
        anomaly_threshold
    )

    result = pd.DataFrame(
        {
            "anomaly_score": anomaly_scores,
            "anomaly_threshold": (
                np.full(
                    len(records),
                    anomaly_threshold,
                    dtype=np.float64,
                )
            ),
            "threshold_margin": (
                threshold_margins
            ),
            "is_anomaly": predictions,
        },
        index=records.index.copy(),
    )

    return result


def score_operational_record(
    record: Mapping[str, Any],
    *,
    artifact_bundle: dict[str, Any] | None = None,
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> dict[str, float | bool]:
    """Score one operational behavioral record."""

    if not isinstance(
        record,
        Mapping,
    ):
        raise TypeError(
            "A single operational record must be "
            "provided as a mapping."
        )

    records = pd.DataFrame(
        [dict(record)]
    )

    result = score_operational_records(
        records,
        artifact_bundle=artifact_bundle,
        model_path=model_path,
    )

    row = result.iloc[0]

    return {
        "anomaly_score": float(
            row["anomaly_score"]
        ),
        "anomaly_threshold": float(
            row["anomaly_threshold"]
        ),
        "threshold_margin": float(
            row["threshold_margin"]
        ),
        "is_anomaly": bool(
            row["is_anomaly"]
        ),
    }
