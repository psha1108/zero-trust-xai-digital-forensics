import pytest

from ml.explainability.shap.builder import build_explanation


def test_build_explanation_creates_contract():
    result = build_explanation(
        prediction="high",
        base_value=0.25,
        feature_names=["login_hour", "is_new_ip", "access_count_5min"],
        contributions=[0.10, -0.05, 0.20],
    )

    assert result.prediction == "high"
    assert result.base_value == 0.25
    assert len(result.contributions) == 3

    assert result.contributions[0].feature_name == "login_hour"
    assert result.contributions[0].contribution == pytest.approx(0.10)

    assert result.contributions[1].feature_name == "is_new_ip"
    assert result.contributions[1].contribution == pytest.approx(-0.05)

    assert result.contributions[2].feature_name == "access_count_5min"
    assert result.contributions[2].contribution == pytest.approx(0.20)


def test_build_explanation_preserves_feature_order():
    feature_names = ["feature_a", "feature_b", "feature_c"]
    contributions = [0.1, 0.2, 0.3]

    result = build_explanation(
        prediction="low",
        base_value=0.5,
        feature_names=feature_names,
        contributions=contributions,
    )

    assert [item.feature_name for item in result.contributions] == feature_names


def test_build_explanation_rejects_length_mismatch():
    with pytest.raises(
        ValueError,
        match="Feature names and contributions must have the same length",
    ):
        build_explanation(
            prediction="medium",
            base_value=0.3,
            feature_names=["feature_a", "feature_b"],
            contributions=[0.1],
        )


def test_build_explanation_converts_contributions_to_float():
    result = build_explanation(
        prediction="high",
        base_value=0,
        feature_names=["feature_a", "feature_b"],
        contributions=[1, 2],
    )

    assert all(
        isinstance(item.contribution, float)
        for item in result.contributions
    )
