"""Utilities for explicit multiclass SHAP handling."""

from collections.abc import Sequence


def get_class_index(
    class_names: Sequence[str],
    class_name: str,
) -> int:
    """Return the actual model class index for a class name."""
    classes = list(class_names)

    if class_name not in classes:
        raise ValueError(
            f"Unknown class '{class_name}'. Available classes: {classes}"
        )

    return classes.index(class_name)


def validate_class_order(
    actual_classes: Sequence[str],
    expected_classes: Sequence[str],
) -> None:
    """Validate the exact class order used by the model."""
    actual = list(actual_classes)
    expected = list(expected_classes)

    if actual != expected:
        raise ValueError(
            "Class order mismatch. "
            f"Expected {expected}, got {actual}."
        )


def build_class_metadata(
    class_names: Sequence[str],
    explained_class: str,
) -> dict[str, object]:
    """Build explicit metadata for the explained class."""
    classes = list(class_names)
    class_index = get_class_index(classes, explained_class)

    return {
        "class_order": classes,
        "explained_class": explained_class,
        "explained_class_index": class_index,
    }
