import pytest

from ml.explainability.shap.multiclass import (
    build_class_metadata,
    get_class_index,
    validate_class_order,
)


def test_get_class_index_uses_actual_model_order():
    classes = ["high", "low", "medium"]

    assert get_class_index(classes, "high") == 0
    assert get_class_index(classes, "low") == 1
    assert get_class_index(classes, "medium") == 2


def test_get_class_index_rejects_unknown_class():
    classes = ["high", "low", "medium"]

    with pytest.raises(ValueError, match="Unknown class"):
        get_class_index(classes, "critical")


def test_validate_class_order_accepts_exact_order():
    actual = ["high", "low", "medium"]
    expected = ["high", "low", "medium"]

    validate_class_order(actual, expected)


def test_validate_class_order_rejects_wrong_order():
    actual = ["low", "medium", "high"]
    expected = ["high", "low", "medium"]

    with pytest.raises(ValueError, match="Class order mismatch"):
        validate_class_order(actual, expected)


def test_build_class_metadata_records_explained_class():
    classes = ["high", "low", "medium"]

    result = build_class_metadata(classes, "high")

    assert result == {
        "class_order": ["high", "low", "medium"],
        "explained_class": "high",
        "explained_class_index": 0,
    }


def test_build_class_metadata_records_medium_index():
    classes = ["high", "low", "medium"]

    result = build_class_metadata(classes, "medium")

    assert result["explained_class"] == "medium"
    assert result["explained_class_index"] == 2
