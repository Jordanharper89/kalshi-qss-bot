
from qseries_v2.integration.canonical_prediction_contract import *

def test_int_003():

    explanation = PredictionExplanation(
        summary="Bullish edge",
        reasons=["Momentum","Liquidity"],
        evidence={"sample":5},
    )

    prediction = CanonicalPredictionFactory.create(
        engine_id="oracle.pattern",
        market_id="KX-001",
        direction=PredictionDirection.YES,
        confidence=0.86,
        score=0.23,
        probability=0.71,
        expected_value=0.12,
        risk=0.18,
        features={"pattern":"breakout"},
        explanation=explanation,
    )

    validation = CanonicalPredictionValidator.validate(prediction)

    assert validation["status"] == "ok"
    assert prediction.direction == PredictionDirection.YES
    assert prediction.metrics.confidence == 0.86
    assert prediction.identity.engine_id == "oracle.pattern"
    assert prediction.explanation.summary == "Bullish edge"

    print("[PASS] INT-003 Canonical Prediction Contract")
    print(prediction.to_dict())

if __name__ == "__main__":
    test_int_003()
