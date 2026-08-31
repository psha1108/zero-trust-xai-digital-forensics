"""SHAP TreeExplainer integration for the official Random Forest."""

from pathlib import Path
from typing import Any

import shap

from ml.explainability.shap.random_forest import (
    DEFAULT_RF_BUNDLE_PATH,
    load_random_forest_bundle,
)


def create_random_forest_explainer(
    bundle_path: str | Path = DEFAULT_RF_BUNDLE_PATH,
) -> tuple[dict[str, Any], shap.TreeExplainer]:
    """Load the official RF bundle and create its SHAP TreeExplainer."""
    bundle = load_random_forest_bundle(bundle_path)

    model = bundle["model"]

    explainer = shap.TreeExplainer(model)

    return bundle, explainer
