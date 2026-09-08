"""Utilities for generating human-readable explanations from existing XAI and policy data."""

from typing import Any


def generate_shap_explanation(shap_data: dict[str, Any]) -> str:
    """Generate a human-readable explanation from existing SHAP contributions."""
    if not shap_data:
        return "Detailed SHAP explanation unavailable for this event."
        
    explanation = shap_data.get("explanation", {})
    contributions = explanation.get("contributions") or shap_data.get("contributions")
    
    if not contributions or not isinstance(contributions, list):
        return "Detailed SHAP explanation unavailable for this event."
        
    predicted_class = shap_data.get("prediction") or explanation.get("prediction")
    pred_text = f"{predicted_class}-risk prediction" if predicted_class else "model's prediction"

    # Filter out zero contributions
    valid_contribs = []
    for c in contributions:
        name = c.get("feature_name")
        val = c.get("contribution")
        if name and isinstance(val, (int, float)) and abs(val) > 1e-6:
            valid_contribs.append({"feature": name, "value": float(val)})

    if not valid_contribs:
        return "No single feature strongly influenced the risk prediction."

    # Sort by absolute magnitude
    valid_contribs.sort(key=lambda x: abs(x["value"]), reverse=True)
    
    # Feature name translations for readability
    feature_translations = {
        "failed_attempt_count": "number of failed attempts",
        "access_count_5min": "access frequency",
        "is_unusual_time": "unusual access timing",
        "is_new_ip": "new IP address",
        "is_new_device": "new device fingerprint",
        "session_duration_minutes": "session duration",
        "resource_sensitivity_score": "resource sensitivity",
        "unauthorized_access_attempt": "unauthorized access attempt",
        "ip_changed_during_session": "IP address change",
        "device_changed_during_session": "device change",
        "sensitive_resource_access_count": "sensitive resource access count",
        "role_admin": "admin role",
        "role_employee": "employee role",
        "role_finance_user": "finance role",
        "role_guest": "guest role",
        "role_hr_user": "HR role",
        "login_hour": "login hour",
        "is_working_hour": "working hour status",
    }

    sentences = []
    
    for i, contrib in enumerate(valid_contribs[:3]): # Top 3 contributors
        feature = contrib["feature"]
        val = contrib["value"]
        
        readable_feature = feature_translations.get(feature, feature.replace("_", " "))
            
        if i == 0:
            if val > 0:
                sentences.append(f"SHAP analysis indicates that the {readable_feature} was the strongest contributor to the {pred_text}.")
            else:
                sentences.append(f"SHAP analysis indicates that the {readable_feature} most strongly reduced the model's predicted risk.")
        else:
            if val > 0:
                sentences.append(f"The {readable_feature} also contributed to the {pred_text}.")
            else:
                sentences.append(f"The {readable_feature} reduced the model's predicted risk.")

    return " ".join(sentences)


def generate_policy_explanation(action: str, reason_codes: list[str]) -> str:
    """Generate a human-readable explanation from existing policy action and reason codes."""
    if not action:
        return "Detailed policy reason unavailable for this event."
        
    action = action.strip().upper()
    
    # Translate reason codes
    reason_map = {
        "low_risk_routine_authorized": "low risk and satisfied access-control conditions",
        "rf_medium_risk": "the assessment indicated medium risk",
        "rf_high_risk": "the assessment indicated high risk",
        "isolation_forest_anomaly": "an anomaly was detected in the session behaviour",
        "elevated_behavior": "elevated behavioural activity was observed",
        "privilege_mismatch": "a privilege mismatch was detected",
    }
    
    reasons_text = []
    if reason_codes:
        for code in reason_codes:
            translated = reason_map.get(code)
            if translated:
                reasons_text.append(translated)
            else:
                reasons_text.append(code.replace("_", " "))
                
    reasons_clause = " and ".join(reasons_text) if reasons_text else "an unspecified condition"
    
    if action == "ALLOW":
        if reason_codes and "low_risk_routine_authorized" in reason_codes:
            return "Access was allowed because the request was assessed as low risk and satisfied the applicable Zero Trust access-control conditions."
        return f"Access was allowed because {reasons_clause}."
        
    elif action == "OTP":
        base = "Step-up verification was required because"
        if reasons_text:
            return f"{base} {reasons_clause}, while not meeting the conditions for session termination."
        return f"{base} the current security assessment indicated increased risk while not meeting the conditions for session termination."
        
    elif action == "RESTRICT":
        base = "Access was restricted because"
        if reasons_text:
            return f"{base} {reasons_clause}."
        return f"{base} the request did not satisfy the applicable Zero Trust policy conditions."
        
    elif action == "BLOCK":
        base = "The current session was terminated because"
        if reasons_text:
            return f"{base} {reasons_clause}, requiring the session to be stopped."
        return f"{base} the security assessment reached a high-risk condition requiring the session to be stopped."
        
    return "Detailed policy reason unavailable for this event."
