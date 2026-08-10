"""Reusable inference functions for the operational Random Forest."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ml.classification.fingerprinting import (
    calculate_random_forest_semantic_fingerprint,
)
from ml.classification.preprocessing import (
    MODEL_FEATURE_COLUMNS,
    ROLE_CATEGORIES,
    get_transformed_feature_names,
    get_transformed_source_feature_mapping,
    transform_random_forest_features,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_MODEL_PATH = (
    PROJECT_ROOT
    / "model_artifacts"
    / "operational"
    / "random_forest_risk_bundle.joblib"
)

EXPECTED_ARTIFACT_SCHEMA_VERSION = 1

EXPECTED_MODEL_NAME = "operational_random_forest"

EXPECTED_MODEL_TYPE = "RandomForestClassifier"

EXPECTED_SELECTED_CANDIDATE_ID = "rf_baseline"

EXPECTED_CLASS_ORDER = [
    "high",
    "low",
    "medium",
]

REQUIRED_ARTIFACT_FIELDS = {
    "artifact_schema_version",
    "model_name",
    "model_type",
    "selected_candidate_id",
    "preprocessor",
    "model",
    "semantic_fingerprint",
    "source_feature_columns",
    "transformed_feature_columns",
    "transformed_source_feature_mapping",
    "role_categories",
    "class_order",
    "model_parameters",
    "target_column",
    "probability_definition",
}


def validate_random_forest_bundle(
    artifact_bundle: dict[str, Any],
) -> None:
    """Validate the loaded Random Forest artifact contract."""

    if not isinstance(
        artifact_bundle,
        dict,
    ):
        raise TypeError(
            "Random Forest artifact must be a dictionary."
        )

    missing_fields = (
        REQUIRED_ARTIFACT_FIELDS
        -
        set(artifact_bundle)
    )

    if missing_fields:
        raise ValueError(
            "Random Forest artifact is missing fields: "
            f"{sorted(missing_fields)}"
        )

    if artifact_bundle[
        "artifact_schema_version"
    ] != EXPECTED_ARTIFACT_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported Random Forest artifact schema: "
            f"{artifact_bundle['artifact_schema_version']}"
        )

    if artifact_bundle[
        "model_name"
    ] != EXPECTED_MODEL_NAME:
        raise ValueError(
            "Unexpected Random Forest model name."
        )

    if artifact_bundle[
        "model_type"
    ] != EXPECTED_MODEL_TYPE:
        raise ValueError(
            "Unexpected Random Forest model type."
        )

    if artifact_bundle[
        "selected_candidate_id"
    ] != EXPECTED_SELECTED_CANDIDATE_ID:
        raise ValueError(
            "Unexpected Random Forest selected candidate."
        )

    if artifact_bundle[
        "source_feature_columns"
    ] != list(MODEL_FEATURE_COLUMNS):
        raise ValueError(
            "Random Forest source-feature contract changed."
        )

    if artifact_bundle[
        "role_categories"
    ] != list(ROLE_CATEGORIES):
        raise ValueError(
            "Random Forest role-category contract changed."
        )

    if artifact_bundle[
        "class_order"
    ] != EXPECTED_CLASS_ORDER:
        raise ValueError(
            "Random Forest class-order contract changed."
        )

    if artifact_bundle[
        "target_column"
    ] != "risk_label":
        raise ValueError(
            "Unexpected Random Forest target column."
        )

    model = artifact_bundle[
        "model"
    ]

    if not hasattr(
        model,
        "predict",
    ):
        raise ValueError(
            "Artifact model does not support predict()."
        )

    if not hasattr(
        model,
        "predict_proba",
    ):
        raise ValueError(
            "Artifact model does not support predict_proba()."
        )

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
            "Random Forest model.classes_ does not match "
            "the stored class order."
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

    actual_transformed_features = (
        get_transformed_feature_names(
            preprocessor
        )
    )

    if (
        actual_transformed_features
        != artifact_bundle[
            "transformed_feature_columns"
        ]
    ):
        raise ValueError(
            "Random Forest transformed-feature contract changed."
        )

    actual_mapping = (
        get_transformed_source_feature_mapping(
            preprocessor
        )
    )

    if (
        actual_mapping
        != artifact_bundle[
            "transformed_source_feature_mapping"
        ]
    ):
        raise ValueError(
            "Random Forest transformed/source mapping changed."
        )

    calculated_fingerprint = (
        calculate_random_forest_semantic_fingerprint(
            artifact_bundle
        )
    )

    if (
        calculated_fingerprint
        != artifact_bundle[
            "semantic_fingerprint"
        ]
    ):
        raise ValueError(
            "Random Forest semantic fingerprint mismatch."
        )


def load_random_forest_bundle(
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> dict[str, Any]:
    """Load and validate the operational Random Forest bundle."""

    resolved_path = Path(
        model_path
    ).resolve()

    if not resolved_path.is_file():
        raise FileNotFoundError(
            "Random Forest artifact was not found: "
            f"{resolved_path}"
        )

    artifact_bundle = joblib.load(
        resolved_path
    )

    validate_random_forest_bundle(
        artifact_bundle
    )

    return artifact_bundle


def classify_operational_records(
    records: pd.DataFrame,
    *,
    artifact_bundle: dict[str, Any] | None = None,
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> pd.DataFrame:
    """Classify one or more operational behavioral records.

    Probability columns are explicitly named by risk class rather
    than relying on positional interpretation of predict_proba().
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
            load_random_forest_bundle(
                model_path
            )
        )
    else:
        validate_random_forest_bundle(
            artifact_bundle
        )

    transformed_matrix = (
        transform_random_forest_features(
            artifact_bundle[
                "preprocessor"
            ],
            records,
        )
    )

    model = artifact_bundle[
        "model"
    ]

    predictions = np.asarray(
        model.predict(
            transformed_matrix
        )
    ).astype(str)

    probabilities = np.asarray(
        model.predict_proba(
            transformed_matrix
        ),
        dtype=np.float64,
    )

    class_order = list(
        artifact_bundle[
            "class_order"
        ]
    )

    if predictions.shape != (
        len(records),
    ):
        raise RuntimeError(
            "Random Forest returned an unexpected "
            "number of predictions."
        )

    if probabilities.shape != (
        len(records),
        len(class_order),
    ):
        raise RuntimeError(
            "Random Forest returned an unexpected "
            "probability matrix shape."
        )

    if not np.isfinite(
        probabilities
    ).all():
        raise RuntimeError(
            "Random Forest returned non-finite probabilities."
        )

    np.testing.assert_allclose(
        probabilities.sum(
            axis=1
        ),
        np.ones(
            len(records),
            dtype=np.float64,
        ),
        rtol=0.0,
        atol=1e-12,
    )

    class_to_index = {
        label: index
        for index, label in enumerate(
            class_order
        )
    }

    result = pd.DataFrame(
        {
            "predicted_risk": predictions,
            "probability_low": probabilities[
                :,
                class_to_index["low"],
            ],
            "probability_medium": probabilities[
                :,
                class_to_index["medium"],
            ],
            "probability_high": probabilities[
                :,
                class_to_index["high"],
            ],
        },
        index=records.index.copy(),
    )

    return result


def classify_operational_record(
    record: Mapping[str, Any],
    *,
    artifact_bundle: dict[str, Any] | None = None,
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> dict[str, str | float]:
    """Classify one operational behavioral record."""

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

    result = classify_operational_records(
        records,
        artifact_bundle=artifact_bundle,
        model_path=model_path,
    )

    row = result.iloc[0]

    return {
        "predicted_risk": str(
            row["predicted_risk"]
        ),
        "probability_low": float(
            row["probability_low"]
        ),
        "probability_medium": float(
            row["probability_medium"]
        ),
        "probability_high": float(
            row["probability_high"]
        ),
    }
