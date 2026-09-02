"""Backend orchestration for operational RF + SHAP + K-Means analysis."""

from __future__ import annotations

from typing import Any

from flask import has_app_context

from app.extensions import db
from app.models import Session
from app.services.operational_features import (
    build_operational_feature_record_from_database,
)
from ml.classification.inference import (
    classify_operational_record,
)
from ml.clustering.inference import (
    cluster_operational_record,
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


def _persist_behavioral_cluster(
    *,
    session_id: str,
    cluster_id: int,
) -> None:
    """
    Persist the canonical behavioral cluster on the session login event.

    Unit-level orchestration tests may call the service without a Flask
    application context. Real HTTP/database execution always has one.
    """

    if not has_app_context():
        return

    session_row = Session.query.filter_by(
        session_id=session_id,
    ).first()

    if session_row is None:
        raise ValueError(
            "Cannot persist behavioral cluster: "
            f"session {session_id!r} does not exist."
        )

    login_event = session_row.login_event

    if login_event is None:
        raise ValueError(
            "Cannot persist behavioral cluster: "
            "session has no linked login event."
        )

    login_event.cluster_id = int(
        cluster_id
    )

    db.session.commit()


def _validate_behavioral_cluster(
    payload: Any,
) -> dict[str, Any]:
    """Validate the behavior-only K-Means inference payload."""

    if not isinstance(
        payload,
        dict,
    ):
        raise TypeError(
            "K-Means behavioral cluster payload must be a dictionary."
        )

    if set(
        payload
    ) != {
        "cluster_id",
        "archetype_name",
    }:
        raise ValueError(
            "K-Means behavioral cluster payload must contain exactly "
            "cluster_id and archetype_name."
        )

    cluster_id = payload[
        "cluster_id"
    ]

    archetype_name = payload[
        "archetype_name"
    ]

    if (
        not isinstance(
            cluster_id,
            int,
        )
        or isinstance(
            cluster_id,
            bool,
        )
    ):
        raise TypeError(
            "K-Means cluster_id must be an integer."
        )

    if cluster_id not in {
        0,
        1,
    }:
        raise ValueError(
            "K-Means canonical cluster_id must be 0 or 1."
        )

    expected_names = {
        0: "Elevated Behavioral Activity",
        1: "Routine Behavioral Activity",
    }

    if archetype_name != expected_names[
        cluster_id
    ]:
        raise ValueError(
            "K-Means cluster_id/archetype_name mismatch."
        )

    return {
        "cluster_id": cluster_id,
        "archetype_name": archetype_name,
    }


def analyze_operational_access(
    *,
    session_id: str,
    access_event_id: int,
) -> dict[str, Any]:
    """
    Analyze one persisted operational access event.

    The exact 14-feature dictionary is constructed once and the same
    dictionary object is supplied to Random Forest, SHAP, and K-Means.

    Random Forest supplies the supervised risk classification.
    SHAP explains that Random Forest prediction.
    K-Means supplies behavioral context only.

    Zero Trust policy enforcement remains intentionally outside this
    service.
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

    behavioral_cluster = (
        _validate_behavioral_cluster(
            cluster_operational_record(
                features
            )
        )
    )

    _persist_behavioral_cluster(
        session_id=session_id,
        cluster_id=behavioral_cluster[
            "cluster_id"
        ],
    )

    return {
        "features": features,
        "prediction": prediction,
        "behavioral_cluster": behavioral_cluster,
        "explanation": explanation,
    }
