from typing import Any

import numpy as np


def normalize_shap_values(shap_values: Any) -> list[np.ndarray]:
    """Normalize common SHAP output formats into a list of arrays."""
    if isinstance(shap_values, list):
        return [np.asarray(values) for values in shap_values]

    values = np.asarray(shap_values)

    if values.ndim == 2:
        return [values]

    if values.ndim == 3:
        return [values[:, :, index] for index in range(values.shape[2])]

    raise ValueError(
        "Unsupported SHAP value shape. Expected a list, 2D array, or 3D array."
    )
