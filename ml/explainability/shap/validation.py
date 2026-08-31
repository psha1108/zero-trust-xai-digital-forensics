"""Validation utilities for SHAP feature contracts."""

from collections.abc import Mapping, Sequence


def validate_feature_order(
    expected_features: Sequence[str],
    actual_features: Sequence[str],
) -> None:
    """Validate that feature names and order match exactly."""
    expected = list(expected_features)
    actual = list(actual_features)

    if expected != actual:
        raise ValueError(
            "Feature order mismatch. "
            f"Expected {expected}, got {actual}."
        )


def validate_transformed_to_source_mapping(
    transformed_feature_names: Sequence[str],
    source_feature_names: Sequence[str],
    transformed_to_source: Mapping[str, str],
) -> None:
    """Validate the transformed-to-source feature mapping."""
    transformed = list(transformed_feature_names)
    source = set(source_feature_names)

    missing = [
        name for name in transformed
        if name not in transformed_to_source
    ]
    if missing:
        raise ValueError(
            f"Missing source mapping for transformed features: {missing}"
        )

    unknown = [
        name
        for name in transformed_to_source
        if name not in transformed
    ]
    if unknown:
        raise ValueError(
            f"Mapping contains unknown transformed features: {unknown}"
        )

    invalid_sources = sorted(
        {
            transformed_to_source[name]
            for name in transformed
            if transformed_to_source[name] not in source
        }
    )
    if invalid_sources:
        raise ValueError(
            f"Mapping contains unknown source features: {invalid_sources}"
        )
