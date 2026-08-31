"""Integration helpers for the official Random Forest SHAP workflow."""

from pathlib import Path
from typing import Any

import joblib


DEFAULT_RF_BUNDLE_PATH = Path(
    "model_artifacts/operational/random_forest_risk_bundle.joblib"
)


def load_random_forest_bundle(
    bundle_path: str | Path = DEFAULT_RF_BUNDLE_PATH,
) -> dict[str, Any]:
    """Load and validate the official Random Forest bundle."""
    path = Path(bundle_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Random Forest bundle not found: {path}"
        )

    bundle = joblib.load(path)

    if not isinstance(bundle, dict):
        raise ValueError("Random Forest bundle must be a dictionary.")

    required_keys = {
        "preprocessor",
        "model",
        "source_feature_columns",
        "transformed_feature_columns",
        "transformed_source_feature_mapping",
        "class_order",
        "semantic_fingerprint",
    }

    missing_keys = required_keys.difference(bundle)

    if missing_keys:
        raise ValueError(
            f"Random Forest bundle is missing required keys: "
            f"{sorted(missing_keys)}"
        )

    model = bundle["model"]
    class_order = list(bundle["class_order"])

    if list(model.classes_) != class_order:
        raise ValueError(
            "Model class order does not match bundle class order."
        )

    transformed_features = bundle["transformed_feature_columns"]

    if model.n_features_in_ != len(transformed_features):
        raise ValueError(
            "Model input feature count does not match transformed "
            "feature count."
        )

    return bundle
