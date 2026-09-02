from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ShapFeatureContribution:
    """SHAP contribution for one source feature."""

    feature_name: str
    contribution: float


@dataclass(frozen=True)
class ShapExplanation:
    """Model-independent representation of one SHAP explanation."""

    prediction: Any
    base_value: Any
    contributions: tuple[ShapFeatureContribution, ...]
