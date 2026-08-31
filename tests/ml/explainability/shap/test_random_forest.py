import joblib
import pytest

from ml.explainability.shap.random_forest import (
    load_random_forest_bundle,
)


BUNDLE_PATH = "model_artifacts/operational/random_forest_risk_bundle.joblib"


def test_load_random_forest_bundle_returns_official_bundle():
    bundle = load_random_forest_bundle(BUNDLE_PATH)

    assert isinstance(bundle, dict)
    assert bundle["model_name"] == "operational_random_forest"
    assert bundle["model_type"] == "RandomForestClassifier"


def test_load_random_forest_bundle_preserves_class_order():
    bundle = load_random_forest_bundle(BUNDLE_PATH)

    assert list(bundle["model"].classes_) == ["high", "low", "medium"]
    assert bundle["class_order"] == ["high", "low", "medium"]


def test_load_random_forest_bundle_matches_feature_contract():
    bundle = load_random_forest_bundle(BUNDLE_PATH)

    assert len(bundle["source_feature_columns"]) == 14
    assert len(bundle["transformed_feature_columns"]) == 18
    assert bundle["model"].n_features_in_ == 18


def test_load_random_forest_bundle_rejects_missing_file():
    with pytest.raises(FileNotFoundError):
        load_random_forest_bundle("does_not_exist.joblib")


def test_load_random_forest_bundle_rejects_invalid_bundle(
    tmp_path,
):
    invalid_path = tmp_path / "invalid.joblib"

    joblib.dump({"model": "not-a-model"}, invalid_path)

    with pytest.raises(ValueError, match="missing required keys"):
        load_random_forest_bundle(invalid_path)
