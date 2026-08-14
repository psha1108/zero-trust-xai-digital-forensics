from typing import Any

from ml.explainability.shap.contracts import ShapExplanation


def explanation_to_dict(explanation: ShapExplanation) -> dict[str, Any]:
    """Convert a SHAP explanation contract into a JSON-safe dictionary."""
    return {
        "prediction": explanation.prediction,
        "base_value": explanation.base_value,
        "contributions": [
            {
                "feature_name": contribution.feature_name,
                "contribution": contribution.contribution,
            }
            for contribution in explanation.contributions
        ],
    }
