from collections import defaultdict
from typing import Mapping, Sequence

import numpy as np


def aggregate_shap_values(
    shap_values: np.ndarray,
    transformed_to_source: Mapping[str, str],
    transformed_feature_names: Sequence[str],
    source_feature_names: Sequence[str],
) -> np.ndarray:
    """Aggregate transformed-feature SHAP values into source features."""
    values = np.asarray(shap_values)

    if values.ndim != 2:
        raise ValueError("SHAP values must be a 2D array.")

    if values.shape[1] != len(transformed_feature_names):
        raise ValueError(
            "SHAP value columns must match transformed feature names."
        )

    missing_sources = [
        name
        for name in transformed_feature_names
        if name not in transformed_to_source
    ]
    if missing_sources:
        raise ValueError(
            f"Missing source mapping for transformed features: {missing_sources}"
        )

    source_index = {
        name: index for index, name in enumerate(source_feature_names)
    }

    unknown_sources = {
        transformed_to_source[name]
        for name in transformed_feature_names
        if transformed_to_source[name] not in source_index
    }
    if unknown_sources:
        raise ValueError(
            f"Mapping contains unknown source features: {sorted(unknown_sources)}"
        )

    aggregated = np.zeros(
        (values.shape[0], len(source_feature_names)),
        dtype=float,
    )

    for transformed_index, transformed_name in enumerate(
        transformed_feature_names
    ):
        source_name = transformed_to_source[transformed_name]
        aggregated[:, source_index[source_name]] += values[:, transformed_index]

    return aggregated
