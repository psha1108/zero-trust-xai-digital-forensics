"""Backend orchestration for operational Random Forest + SHAP analysis."""

from __future__ import annotations

from typing import Any

from app.services.operational_features import (
    build_operational_feature_record_from_database,
)
from ml.classification.inference import (
    classify_operational_record,
)
from ml.explainability.shap.contracts import (
    ShapExplanation,
)
from ml.explainability.shap.pipeline import (
    explain_random_forest_prediction,
)
from ml.explainability.shap.serialization import (
    explanation_to_dict,
)


def analyze_operational_access(
    *,
    session_id: str,
    access_event_id: int,
) -> dict[str, Any]:
    """
    Classify and explain one persisted operational access event.

    The operational feature record is constructed exactly once and the
    same dictionary object is supplied to both Random Forest inference
    and SHAP explainability.

    Policy enforcement is intentionally outside this service.
    """

    features = build_operational_feature_record_from_database(
        session_id=session_id,
        access_event_id=access_event_id,
    )

    prediction = classify_operational_record(
        features
    )

    explanation = explain_random_forest_prediction(
        features
    )

    predicted_risk = prediction.get(
        "predicted_risk"
    )

    explained_prediction = explanation.get(
        "prediction"
    )

    if predicted_risk != explained_prediction:
        raise ValueError(
            "Random Forest prediction/explanation class mismatch: "
            f"prediction={predicted_risk!r}, "
            f"explanation={explained_prediction!r}."
        )

    explanation_contract = explanation.get(
        "explanation"
    )

    if isinstance(
        explanation_contract,
        ShapExplanation,
    ):
        explanation = {
            **explanation,
            "explanation": explanation_to_dict(
                explanation_contract
            ),
        }
    elif not isinstance(
        explanation_contract,
        dict,
    ):
        raise TypeError(
            "SHAP explanation payload must be a "
            "ShapExplanation or dictionary."
        )

    return {
        "features": features,
        "prediction": prediction,
        "explanation": explanation,
    }