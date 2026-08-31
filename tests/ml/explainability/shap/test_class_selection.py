import numpy as np
import pytest

from ml.explainability.shap.class_selection import (
    select_class_shap_values,
)


def test_select_class_shap_values_returns_requested_class():
    shap_values = np.array(
        [
            [
                [1.0, 10.0, 100.0],
                [2.0, 20.0, 200.0],
            ]
        ]
    )

    result = select_class_shap_values(shap_values, class_index=1)

    expected = np.array([[10.0, 20.0]])

    np.testing.assert_array_equal(result, expected)


def test_select_class_shap_values_preserves_sample_and_feature_shape():
    shap_values = np.zeros((2, 18, 3))

    result = select_class_shap_values(shap_values, class_index=2)

    assert result.shape == (2, 18)


def test_select_class_shap_values_rejects_wrong_shape():
    shap_values = np.zeros((18, 3))

    with pytest.raises(ValueError, match="Expected multiclass SHAP values"):
        select_class_shap_values(shap_values, class_index=0)


def test_select_class_shap_values_rejects_invalid_class_index():
    shap_values = np.zeros((1, 18, 3))

    with pytest.raises(IndexError, match="out of range"):
        select_class_shap_values(shap_values, class_index=3)
