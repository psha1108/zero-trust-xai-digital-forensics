import numpy as np

from ml.explainability.shap.aggregation import aggregate_shap_values


def test_aggregate_transformed_features_to_source_features():
    shap_values = np.array([
        [1.0, 2.0, 3.0, 4.0],
        [0.5, 1.5, 2.5, 3.5],
    ])

    transformed_features = [
        "role_admin",
        "role_guest",
        "login_hour",
        "is_new_ip",
    ]

    source_features = [
        "role",
        "login_hour",
        "is_new_ip",
    ]

    mapping = {
        "role_admin": "role",
        "role_guest": "role",
        "login_hour": "login_hour",
        "is_new_ip": "is_new_ip",
    }

    result = aggregate_shap_values(
        shap_values,
        mapping,
        transformed_features,
        source_features,
    )

    expected = np.array([
        [3.0, 3.0, 4.0],
        [2.0, 2.5, 3.5],
    ])

    assert np.allclose(result, expected)


def test_aggregate_preserves_source_feature_order():
    shap_values = np.array([[10.0, 20.0, 30.0]])

    transformed_features = [
        "feature_c",
        "feature_a",
        "feature_b",
    ]

    source_features = [
        "feature_a",
        "feature_b",
        "feature_c",
    ]

    mapping = {
        "feature_c": "feature_c",
        "feature_a": "feature_a",
        "feature_b": "feature_b",
    }

    result = aggregate_shap_values(
        shap_values,
        mapping,
        transformed_features,
        source_features,
    )

    expected = np.array([[20.0, 30.0, 10.0]])

    assert np.allclose(result, expected)


def test_aggregate_rejects_missing_mapping():
    shap_values = np.array([[1.0, 2.0]])

    transformed_features = ["feature_a", "feature_b"]
    source_features = ["feature_a", "feature_b"]

    mapping = {
        "feature_a": "feature_a",
    }

    try:
        aggregate_shap_values(
            shap_values,
            mapping,
            transformed_features,
            source_features,
        )
    except ValueError as exc:
        assert "Missing source mapping" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_aggregate_rejects_invalid_shap_shape():
    shap_values = np.array([1.0, 2.0])

    transformed_features = ["feature_a", "feature_b"]
    source_features = ["feature_a", "feature_b"]

    mapping = {
        "feature_a": "feature_a",
        "feature_b": "feature_b",
    }

    try:
        aggregate_shap_values(
            shap_values,
            mapping,
            transformed_features,
            source_features,
        )
    except ValueError as exc:
        assert "2D array" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
