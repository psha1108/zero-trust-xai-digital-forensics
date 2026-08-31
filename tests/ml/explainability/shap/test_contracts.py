from ml.explainability.shap.contracts import (
    ShapExplanation,
    ShapFeatureContribution,
)


def test_shap_explanation_contract():
    contribution = ShapFeatureContribution(
        feature_name="login_hour",
        contribution=0.18,
    )

    explanation = ShapExplanation(
        prediction="High",
        base_value=0.50,
        contributions=(contribution,),
    )

    assert explanation.prediction == "High"
    assert explanation.base_value == 0.50
    assert len(explanation.contributions) == 1
    assert explanation.contributions[0].feature_name == "login_hour"
    assert explanation.contributions[0].contribution == 0.18
