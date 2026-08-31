import pytest

from ml.explainability.shap.validation import (
    validate_feature_order,
    validate_transformed_to_source_mapping,
)


def test_validate_feature_order_accepts_exact_match():
    expected = ["role", "login_hour", "failed_attempt_count"]
    actual = ["role", "login_hour", "failed_attempt_count"]

    validate_feature_order(expected, actual)


def test_validate_feature_order_rejects_wrong_order():
    expected = ["role", "login_hour", "failed_attempt_count"]
    actual = ["login_hour", "role", "failed_attempt_count"]

    with pytest.raises(ValueError, match="Feature order mismatch"):
        validate_feature_order(expected, actual)


def test_validate_mapping_accepts_valid_mapping():
    transformed = ["role_admin", "role_user", "login_hour"]
    source = ["role", "login_hour"]

    mapping = {
        "role_admin": "role",
        "role_user": "role",
        "login_hour": "login_hour",
    }

    validate_transformed_to_source_mapping(
        transformed,
        source,
        mapping,
    )


def test_validate_mapping_rejects_missing_mapping():
    transformed = ["role_admin", "login_hour"]
    source = ["role", "login_hour"]

    mapping = {
        "role_admin": "role",
    }

    with pytest.raises(ValueError, match="Missing source mapping"):
        validate_transformed_to_source_mapping(
            transformed,
            source,
            mapping,
        )


def test_validate_mapping_rejects_unknown_transformed_feature():
    transformed = ["role_admin"]
    source = ["role"]

    mapping = {
        "role_admin": "role",
        "extra_feature": "role",
    }

    with pytest.raises(
        ValueError,
        match="unknown transformed features",
    ):
        validate_transformed_to_source_mapping(
            transformed,
            source,
            mapping,
        )


def test_validate_mapping_rejects_unknown_source_feature():
    transformed = ["role_admin"]
    source = ["role"]

    mapping = {
        "role_admin": "unknown_source",
    }

    with pytest.raises(
        ValueError,
        match="unknown source features",
    ):
        validate_transformed_to_source_mapping(
            transformed,
            source,
            mapping,
        )
