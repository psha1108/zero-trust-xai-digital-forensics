from ml.explainability.shap.contracts import (
    ShapExplanation,
    ShapFeatureContribution,
)
from ml.explainability.shap.serialization import explanation_to_dict


def test_explanation_to_dict():
    explanation = ShapExplanation(
        prediction="Medium",
        base_value=0.40,
        contributions=(
            ShapFeatureContribution(
                feature_name="failed_attempt_count",
                contribution=0.25,
            ),
            ShapFeatureContribution(
                feature_name="is_new_ip",
                contribution=-0.10,
            ),
        ),
    )

    result = explanation_to_dict(explanation)

    assert result == {
        "prediction": "Medium",
        "base_value": 0.40,
        "contributions": [
            {
                "feature_name": "failed_attempt_count",
                "contribution": 0.25,
            },
            {
                "feature_name": "is_new_ip",
                "contribution": -0.10,
            },
        ],
    }
