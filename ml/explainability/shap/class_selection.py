"""Utilities for selecting class-specific SHAP values."""

import numpy as np


def select_class_shap_values(
    shap_values: np.ndarray,
    class_index: int,
) -> np.ndarray:
    """Select SHAP values for one class from multiclass output."""
    values = np.asarray(shap_values)

    if values.ndim != 3:
        raise ValueError(
            "Expected multiclass SHAP values with shape "
            "(samples, features, classes)."
        )

    if not 0 <= class_index < values.shape[2]:
        raise IndexError(
            f"Class index {class_index} is out of range for "
            f"{values.shape[2]} classes."
        )

    return values[:, :, class_index]
