import numpy as np
import pytest

from ml.explainability.shap.additivity import validate_additivity


def test_additivity_passes_within_tolerance():
    result = validate_additivity(
        base_value=0.2,
        shap_values=np.array([0.1, -0.05, 0.25]),
        model_output=0.5,
    )

    assert result["contribution_sum"] == 0.3
    assert result["reconstructed_output"] == 0.5
    assert result["additivity_error"] <= 1e-6
    assert result["is_additive"] is True


def test_additivity_fails_when_error_exceeds_tolerance():
    result = validate_additivity(
        base_value=0.2,
        shap_values=np.array([0.1, -0.05, 0.25]),
        model_output=0.7,
    )

    assert result["reconstructed_output"] == 0.5
    assert result["additivity_error"] == pytest.approx(0.2)
    assert result["is_additive"] is False


def test_additivity_returns_required_fields():
    result = validate_additivity(
        base_value=0.1,
        shap_values=np.array([0.2, 0.3]),
        model_output=0.6,
    )

    expected_keys = {
        "base_value",
        "contribution_sum",
        "reconstructed_output",
        "model_output",
        "additivity_error",
        "is_additive",
    }

    assert set(result.keys()) == expected_keys
