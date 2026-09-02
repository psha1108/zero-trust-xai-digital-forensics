import numpy as np

from ml.explainability.shap.normalization import normalize_shap_values


def test_normalize_list_output():
    values = [
        np.array([[1.0, 2.0]]),
        np.array([[3.0, 4.0]]),
    ]

    result = normalize_shap_values(values)

    assert len(result) == 2
    assert np.array_equal(result[0], values[0])
    assert np.array_equal(result[1], values[1])


def test_normalize_2d_array():
    values = np.array([
        [1.0, 2.0],
        [3.0, 4.0],
    ])

    result = normalize_shap_values(values)

    assert len(result) == 1
    assert np.array_equal(result[0], values)


def test_normalize_3d_array():
    values = np.array([
        [[1.0, 2.0], [3.0, 4.0]],
        [[5.0, 6.0], [7.0, 8.0]],
    ])

    result = normalize_shap_values(values)

    assert len(result) == 2
    assert result[0].shape == (2, 2)
    assert result[1].shape == (2, 2)


def test_normalize_rejects_unsupported_shape():
    values = np.array([1.0, 2.0, 3.0])

    try:
        normalize_shap_values(values)
    except ValueError as exc:
        assert "Unsupported SHAP value shape" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
