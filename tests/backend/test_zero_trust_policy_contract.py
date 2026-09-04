"""Contract tests for the rule-based Zero Trust policy engine.

The policy layer consumes already-validated ML observations. It must not
retrain models, reinterpret K-Means clusters as risk classes, or mutate
the ML orchestration layer.

Policy actions persisted to the existing VARCHAR(10) ORM columns are:

    Allow
    OTP
    Restrict
    Block

"OTP" is the storage/API token for the user-facing action
"OTP Verification".

Decision precedence:

    Block > Restrict > OTP > Allow

Block requires corroborated ML evidence:
Random Forest == high AND Isolation Forest == anomaly.

K-Means is behavioral context only. Elevated behavior may trigger OTP,
but K-Means alone may never Restrict or Block.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest


VALID_ACTIONS = {
    "Allow",
    "OTP",
    "Restrict",
    "Block",
}


def _analysis(
    *,
    predicted_risk: str,
    is_anomaly: bool,
    cluster_id: int,
) -> dict[str, Any]:
    archetype_name = (
        "Elevated Behavioral Activity"
        if cluster_id == 0
        else "Routine Behavioral Activity"
    )

    return {
        "anomaly_detection": {
            "anomaly_score": 0.60 if is_anomaly else 0.40,
            "anomaly_threshold": 0.5532259181941123,
            "threshold_margin": (
                0.60 - 0.5532259181941123
                if is_anomaly
                else 0.40 - 0.5532259181941123
            ),
            "is_anomaly": is_anomaly,
        },
        "prediction": {
            "predicted_risk": predicted_risk,
        },
        "behavioral_cluster": {
            "cluster_id": cluster_id,
            "archetype_name": archetype_name,
        },
    }


def _decide(
    *,
    predicted_risk: str,
    is_anomaly: bool,
    cluster_id: int,
    privilege_mismatch: bool = False,
) -> dict[str, Any]:
    module = importlib.import_module(
        "app.services.policy_engine"
    )

    return module.decide_zero_trust_policy(
        analysis=_analysis(
            predicted_risk=predicted_risk,
            is_anomaly=is_anomaly,
            cluster_id=cluster_id,
        ),
        privilege_mismatch=privilege_mismatch,
    )


@pytest.mark.parametrize(
    (
        "predicted_risk",
        "is_anomaly",
        "cluster_id",
        "privilege_mismatch",
        "expected_action",
        "expected_terminate",
    ),
    [
        (
            "low",
            False,
            1,
            False,
            "Allow",
            False,
        ),
        (
            "low",
            True,
            1,
            False,
            "OTP",
            False,
        ),
        (
            "low",
            False,
            0,
            False,
            "OTP",
            False,
        ),
        (
            "medium",
            False,
            1,
            False,
            "OTP",
            False,
        ),
        (
            "low",
            False,
            1,
            True,
            "Restrict",
            False,
        ),
        (
            "high",
            False,
            1,
            False,
            "Restrict",
            False,
        ),
        (
            "high",
            True,
            1,
            False,
            "Block",
            True,
        ),
    ],
)
def test_zero_trust_decision_matrix(
    predicted_risk: str,
    is_anomaly: bool,
    cluster_id: int,
    privilege_mismatch: bool,
    expected_action: str,
    expected_terminate: bool,
) -> None:
    result = _decide(
        predicted_risk=predicted_risk,
        is_anomaly=is_anomaly,
        cluster_id=cluster_id,
        privilege_mismatch=privilege_mismatch,
    )

    assert result["action"] == expected_action
    assert result["terminate_session"] is expected_terminate


def test_policy_result_has_small_explicit_contract() -> None:
    result = _decide(
        predicted_risk="low",
        is_anomaly=False,
        cluster_id=1,
    )

    assert set(result) == {
        "action",
        "terminate_session",
        "reason_codes",
    }

    assert result["action"] in VALID_ACTIONS

    # Existing LoginEvent.action_taken and AccessEvent.decision
    # are VARCHAR(10), so every persisted action token must fit.
    assert len(result["action"]) <= 10

    assert isinstance(
        result["terminate_session"],
        bool,
    )

    assert isinstance(
        result["reason_codes"],
        (list, tuple),
    )

    assert result["reason_codes"]


def test_elevated_kmeans_behavior_alone_is_step_up_not_risk_class() -> None:
    result = _decide(
        predicted_risk="low",
        is_anomaly=False,
        cluster_id=0,
        privilege_mismatch=False,
    )

    assert result["action"] == "OTP"
    assert result["terminate_session"] is False

    # K-Means remains behavioral context. Cluster 0 must not be
    # interpreted directly as high risk, Restrict, or Block.
    assert result["action"] not in {
        "Restrict",
        "Block",
    }


def test_block_requires_high_rf_plus_isolation_forest_anomaly() -> None:
    high_only = _decide(
        predicted_risk="high",
        is_anomaly=False,
        cluster_id=1,
    )

    anomaly_only = _decide(
        predicted_risk="low",
        is_anomaly=True,
        cluster_id=1,
    )

    corroborated = _decide(
        predicted_risk="high",
        is_anomaly=True,
        cluster_id=1,
    )

    assert high_only["action"] == "Restrict"
    assert high_only["terminate_session"] is False

    assert anomaly_only["action"] == "OTP"
    assert anomaly_only["terminate_session"] is False

    assert corroborated["action"] == "Block"
    assert corroborated["terminate_session"] is True
