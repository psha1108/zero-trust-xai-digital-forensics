from typing import Any, Sequence

from ml.explainability.shap.contracts import (
    ShapExplanation,
    ShapFeatureContribution,
)


def build_explanation(
    prediction: Any,
    base_value: Any,
    feature_names: Sequence[str],
    contributions: Sequence[float],
) -> ShapExplanation:
    """Build a model-independent SHAP explanation."""

    if len(feature_names) != len(contributions):
        raise ValueError(
            "Feature names and contributions must have the same length."
        )

    feature_contributions = tuple(
        ShapFeatureContribution(
            feature_name=feature_name,
            contribution=float(contribution),
        )
        for feature_name, contribution in zip(
            feature_names,
            contributions,
        )
    )

    return ShapExplanation(
        prediction=prediction,
        base_value=base_value,
        contributions=feature_contributions,
    )
