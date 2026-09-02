"""End-to-end SHAP explanation for the official Random Forest."""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.explainability.shap.additivity import validate_additivity
from ml.explainability.shap.aggregation import aggregate_shap_values
from ml.explainability.shap.class_selection import select_class_shap_values
from ml.explainability.shap.builder import build_explanation
from ml.explainability.shap.explainer import create_random_forest_explainer
from ml.explainability.shap.multiclass import get_class_index


def explain_random_forest_prediction(
    sample: dict[str, Any],
    bundle_path: str | Path | None = None,
):
    """Generate a source-level SHAP explanation for one RF prediction."""

    if bundle_path is None:
        bundle, explainer = create_random_forest_explainer()
    else:
        bundle, explainer = create_random_forest_explainer(bundle_path)

    source_features = bundle["source_feature_columns"]

    missing = [
        feature for feature in source_features
        if feature not in sample
    ]

    extra = [
        feature for feature in sample
        if feature not in source_features
    ]

    if missing:
        raise ValueError(f"Missing source features: {missing}")

    if extra:
        raise ValueError(f"Unknown source features: {extra}")

    sample_df = pd.DataFrame(
        [[sample[feature] for feature in source_features]],
        columns=source_features,
    )

    transformed = bundle["preprocessor"].transform(sample_df)

    if transformed.shape[1] != len(bundle["transformed_feature_columns"]):
        raise ValueError(
            "Transformed feature count does not match bundle contract."
        )

    prediction = bundle["model"].predict(transformed)[0]

    class_index = get_class_index(
        bundle["class_order"],
        prediction,
    )

    shap_values = explainer.shap_values(transformed)

    class_shap_values = select_class_shap_values(
        shap_values,
        class_index=class_index,
    )

    aggregated = aggregate_shap_values(
        class_shap_values,
        bundle["transformed_source_feature_mapping"],
        bundle["transformed_feature_columns"],
        source_features,
    )

    expected_value = np.asarray(explainer.expected_value)

    if expected_value.ndim == 0:
        base_value = float(expected_value)
    else:
        base_value = float(expected_value[class_index])

    model_probability = float(
        bundle["model"].predict_proba(transformed)[0, class_index]
    )

    additivity = validate_additivity(
        base_value=base_value,
        shap_values=aggregated[0],
        model_output=model_probability,
    )

    explanation = build_explanation(
        prediction=prediction,
        base_value=base_value,
        feature_names=source_features,
        contributions=aggregated[0],
    )

    return {
        "explanation": explanation,
        "prediction": prediction,
        "class_index": class_index,
        "class_order": list(bundle["class_order"]),
        "model_probability": model_probability,
        "additivity": additivity,
    }
