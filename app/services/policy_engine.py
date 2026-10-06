"""Rule-based Zero Trust policy decision service.

This module consumes already-computed operational ML observations and
authorization context. It does not run ML models, retrain models, access
the database, mutate sessions, or enforce HTTP responses.

Persisted policy action tokens are intentionally short enough for the
existing VARCHAR(10) columns:

    Allow
    OTP
    Restrict
    Block

Decision precedence:

    Block > Restrict > OTP > Allow

K-Means remains behavioral context only. An elevated behavioral cluster
can request step-up authentication (OTP), but clustering alone cannot
Restrict or Block a session.
"""

from __future__ import annotations

from typing import Any, Mapping


VALID_RISK_LABELS = frozenset({
    "low",
    "medium",
    "high",
})

VALID_CLUSTER_IDS = frozenset({
    0,
    1,
})

VALID_POLICY_ACTIONS = frozenset({
    "Allow",
    "OTP",
    "Restrict",
    "Block",
})


def _extract_policy_evidence(
    analysis: Mapping[str, Any],
) -> tuple[str, bool, int]:
    """Validate and extract the policy-relevant ML observations."""

    if not isinstance(analysis, Mapping):
        raise TypeError(
            "analysis must be a mapping."
        )

    prediction = analysis.get("prediction")
    anomaly_detection = analysis.get(
        "anomaly_detection"
    )
    behavioral_cluster = analysis.get(
        "behavioral_cluster"
    )

    if not isinstance(prediction, Mapping):
        raise TypeError(
            "analysis['prediction'] must be a mapping."
        )

    if not isinstance(
        anomaly_detection,
        Mapping,
    ):
        raise TypeError(
            "analysis['anomaly_detection'] must be a mapping."
        )

    if not isinstance(
        behavioral_cluster,
        Mapping,
    ):
        raise TypeError(
            "analysis['behavioral_cluster'] must be a mapping."
        )

    predicted_risk = prediction.get(
        "predicted_risk"
    )

    if predicted_risk not in VALID_RISK_LABELS:
        raise ValueError(
            "predicted_risk must be low, medium, or high."
        )

    is_anomaly = anomaly_detection.get(
        "is_anomaly"
    )

    if not isinstance(is_anomaly, bool):
        raise TypeError(
            "is_anomaly must be a bool."
        )

    cluster_id = behavioral_cluster.get(
        "cluster_id"
    )

    if isinstance(cluster_id, bool):
        raise TypeError(
            "cluster_id must be an integer."
        )

    if not isinstance(cluster_id, int):
        raise TypeError(
            "cluster_id must be an integer."
        )

    if cluster_id not in VALID_CLUSTER_IDS:
        raise ValueError(
            "cluster_id must be 0 or 1."
        )

    return (
        predicted_risk,
        is_anomaly,
        cluster_id,
    )


def decide_zero_trust_policy(
    *,
    analysis: Mapping[str, Any],
    privilege_mismatch: bool,
    recent_evasion_count: int = 0,
) -> dict[str, Any]:
    """Return the deterministic Zero Trust decision for one access event.

    Policy meanings:

    Allow
        Authorized, low-risk, non-anomalous, routine behavior.

    OTP
        Step-up authentication. Triggered by medium RF risk,
        Isolation Forest anomaly without corroborated high RF risk,
        or elevated K-Means behavioral activity.

    Restrict
        Deny the current access while keeping the session active.
        Triggered by an authorization/privilege mismatch or high RF
        risk without Isolation Forest corroboration.

    Block
        Terminate the session. Requires corroborated evidence:
        RF high risk AND Isolation Forest anomaly.

    K-Means never independently produces Restrict or Block.
    """

    if not isinstance(
        privilege_mismatch,
        bool,
    ):
        raise TypeError(
            "privilege_mismatch must be a bool."
        )

    (
        predicted_risk,
        is_anomaly,
        cluster_id,
    ) = _extract_policy_evidence(
        analysis
    )

    reason_codes: list[str] = []

    # Highest precedence: terminate only when two independent
    # operational models corroborate severe behavior.
    if (
        predicted_risk == "high"
        and is_anomaly
    ):
        reason_codes.extend([
            "rf_high_risk",
            "isolation_forest_anomaly",
        ])

        if privilege_mismatch:
            reason_codes.append(
                "privilege_mismatch"
            )

        if cluster_id == 0:
            reason_codes.append(
                "elevated_behavior"
            )

        return {
            "action": "Block",
            "terminate_session": True,
            "reason_codes": reason_codes,
        }

    # Restrict denies this access but deliberately does not
    # terminate the entire authenticated session.
    if (
        privilege_mismatch
        or predicted_risk == "high"
    ):
        if privilege_mismatch:
            reason_codes.append(
                "privilege_mismatch"
            )

        if predicted_risk == "high":
            reason_codes.append(
                "rf_high_risk"
            )

        if is_anomaly:
            reason_codes.append(
                "isolation_forest_anomaly"
            )

        if cluster_id == 0:
            reason_codes.append(
                "elevated_behavior"
            )

        return {
            "action": "Restrict",
            "terminate_session": False,
            "reason_codes": reason_codes,
        }

    # OTP is adaptive step-up authentication. Elevated K-Means
    # behavior is intentionally allowed to reach only this level.
    if (
        predicted_risk == "medium"
        or is_anomaly
        or cluster_id == 0
    ):
        if predicted_risk == "medium":
            reason_codes.append(
                "rf_medium_risk"
            )

        if is_anomaly:
            reason_codes.append(
                "isolation_forest_anomaly"
            )

        if cluster_id == 0:
            reason_codes.append(
                "elevated_behavior"
            )

        # Escalation: Repeated OTP evasion elevates the risk.
        if recent_evasion_count >= 3:
            reason_codes.append("otp_evasion_detected")
            return {
                "action": "Block",
                "terminate_session": True,
                "reason_codes": reason_codes,
            }
        elif recent_evasion_count >= 2:
            reason_codes.append("otp_evasion_detected")
            return {
                "action": "Restrict",
                "terminate_session": False,
                "reason_codes": reason_codes,
            }

        return {
            "action": "OTP",
            "terminate_session": False,
            "reason_codes": reason_codes,
        }

    return {
        "action": "Allow",
        "terminate_session": False,
        "reason_codes": [
            "low_risk_routine_authorized",
        ],
    }
