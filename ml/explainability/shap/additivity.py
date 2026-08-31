from typing import Any

import numpy as np


def validate_additivity(
    base_value: Any,
    shap_values: Any,
    model_output: Any,
    tolerance: float = 1e-6,
) -> dict[str, float | bool]:
    """Validate SHAP additivity against the supplied model output."""

    base = float(np.asarray(base_value).reshape(-1)[0])
    contributions = np.asarray(shap_values, dtype=float)
    output = float(np.asarray(model_output).reshape(-1)[0])

    contribution_sum = float(np.sum(contributions))
    reconstructed_output = base + contribution_sum
    additivity_error = abs(reconstructed_output - output)

    return {
        "base_value": base,
        "contribution_sum": contribution_sum,
        "reconstructed_output": reconstructed_output,
        "model_output": output,
        "additivity_error": additivity_error,
        "is_additive": bool(additivity_error <= tolerance),
    }
