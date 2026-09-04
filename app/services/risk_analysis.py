"""Unified operational Isolation Forest + RF + SHAP + K-Means analysis."""

from __future__ import annotations

import math
from typing import Any

from flask import has_app_context

from app.extensions import db
from app.models import Session
from app.services.operational_features import (
    build_operational_feature_record_from_database,
)
from ml.anomaly_detection.inference import (
    score_operational_record,
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


def _validate_anomaly_detection(
    payload: Any,
) -> dict[str, float | bool]:
    """Validate the Isolation Forest inference contract."""

    if not isinstance(
        payload,
        dict,
    ):
        raise TypeError(
            "Isolation Forest result must be a dictionary."
        )

    expected_keys = {
        "anomaly_score",
        "anomaly_threshold",
        "threshold_margin",
        "is_anomaly",
    }

    if set(payload) != expected_keys:
        raise ValueError(
            "Isolation Forest result must contain exactly "
            "anomaly_score, anomaly_threshold, "
            "threshold_margin and is_anomaly."
        )

    numeric_values: dict[str, float] = {}

    for key in (
        "anomaly_score",
        "anomaly_threshold",
        "threshold_margin",
    ):
        value = payload[key]

        if (
            isinstance(
                value,
                bool,
            )
            or not isinstance(
                value,
                (int, float),
            )
        ):
            raise TypeError(
                f"Isolation Forest {key} must be numeric."
            )

        numeric_value = float(
            value
        )

        if not math.isfinite(
            numeric_value
        ):
            raise ValueError(
                f"Isolation Forest {key} must be finite."
            )

        numeric_values[key] = numeric_value

    is_anomaly = payload[
        "is_anomaly"
    ]

    if not isinstance(
        is_anomaly,
        bool,
    ):
        raise TypeError(
            "Isolation Forest is_anomaly must be boolean."
        )

    expected_margin = (
        numeric_values[
            "anomaly_score"
        ]
        -
        numeric_values[
            "anomaly_threshold"
        ]
    )

    if not math.isclose(
        numeric_values[
            "threshold_margin"
        ],
        expected_margin,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError(
            "Isolation Forest threshold_margin is inconsistent "
            "with anomaly_score and anomaly_threshold."
        )

    expected_is_anomaly = (
        numeric_values[
            "anomaly_score"
        ]
        >=
        numeric_values[
            "anomaly_threshold"
        ]
    )

    if is_anomaly is not expected_is_anomaly:
        raise ValueError(
            "Isolation Forest is_anomaly is inconsistent "
            "with the frozen threshold rule."
        )

    return {
        "anomaly_score": numeric_values[
            "anomaly_score"
        ],
        "anomaly_threshold": numeric_values[
            "anomaly_threshold"
        ],
        "threshold_margin": numeric_values[
            "threshold_margin"
        ],
        "is_anomaly": is_anomaly,
    }


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


def _persist_model_results(
    *,
    session_id: str,
    anomaly_score: float,
    risk_label: str,
    cluster_id: int,
) -> None:
    """
    Persist model observations on the successful LoginEvent.

    These values are model evidence only. This helper does not set
    action_taken, AccessEvent.decision, or any policy result.
    """

    if not has_app_context():
        return

    session_row = Session.query.filter_by(
        session_id=session_id,
    ).first()

    if session_row is None:
        raise ValueError(
            "Cannot persist ML results: "
            f"session {session_id!r} does not exist."
        )

    login_event = session_row.login_event

    if login_event is None:
        raise ValueError(
            "Cannot persist ML results: "
            "session has no linked login event."
        )

    login_event.anomaly_score = float(
        anomaly_score
    )

    login_event.risk_label = str(
        risk_label
    )

    login_event.cluster_id = int(
        cluster_id
    )

    db.session.commit()


def analyze_operational_access(
    *,
    session_id: str,
    access_event_id: int,
) -> dict[str, Any]:
    """
    Analyze one persisted operational access event with all ML models.

    The exact 14-feature dictionary is constructed once. The identical
    Python dictionary object is supplied to Isolation Forest, Random
    Forest, SHAP, and K-Means.

    Isolation Forest supplies anomaly context.
    Random Forest supplies supervised risk classification.
    SHAP explains the Random Forest prediction.
    K-Means supplies behavioral context only.

    Zero Trust policy enforcement remains intentionally outside this
    service.
    """

    features = build_operational_feature_record_from_database(
        session_id=session_id,
        access_event_id=access_event_id,
    )

    anomaly_detection = (
        _validate_anomaly_detection(
            score_operational_record(
                features
            )
        )
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

    if predicted_risk not in {
        "low",
        "medium",
        "high",
    }:
        raise ValueError(
            "Random Forest predicted_risk must be "
            "low, medium, or high."
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

    _persist_model_results(
        session_id=session_id,
        anomaly_score=anomaly_detection[
            "anomaly_score"
        ],
        risk_label=predicted_risk,
        cluster_id=behavioral_cluster[
            "cluster_id"
        ],
    )

    return {
        "features": features,
        "anomaly_detection": anomaly_detection,
        "prediction": prediction,
        "behavioral_cluster": behavioral_cluster,
        "explanation": explanation,
    }
