
from qseries_v2.integration.canonical_prediction_contract import (
    PredictionDirection,
    PredictionExplanation,
    CanonicalPredictionFactory,
)
from qseries_v2.integration.qseries_execution_gateway import (
    ExecutionDecisionStatus,
    ExecutionRiskLimits,
    QSeriesExecutionGateway,
    create_qseries_execution_gateway,
    qseries_execution_gateway,
)


def test_int_004_qseries_execution_gateway():
    gateway = create_qseries_execution_gateway()

    assert isinstance(gateway, QSeriesExecutionGateway)
    assert qseries_execution_gateway is create_qseries_execution_gateway

    approved_prediction = CanonicalPredictionFactory.create(
        engine_id="oracle.pattern",
        market_id="KX-APPROVE",
        direction=PredictionDirection.YES,
        confidence=0.86,
        score=0.22,
        probability=0.72,
        expected_value=0.08,
        risk=0.20,
        features={"pattern": "breakout"},
        explanation=PredictionExplanation(
            summary="Strong signal",
            reasons=["Momentum", "Liquidity"],
            evidence={"sample_count": 5},
        ),
    )

    approved = gateway.evaluate(approved_prediction)

    assert approved.status == ExecutionDecisionStatus.APPROVED
    assert approved.reasons == []
    assert approved.market_id == "KX-APPROVE"
    assert approved.direction == "YES"

    rejected_prediction = CanonicalPredictionFactory.create(
        engine_id="oracle.pattern",
        market_id="KX-REJECT",
        direction=PredictionDirection.YES,
        confidence=0.55,
        score=0.02,
        probability=0.51,
        expected_value=-0.01,
        risk=0.50,
        features={},
        explanation=None,
    )

    rejected = gateway.evaluate(rejected_prediction)

    assert rejected.status == ExecutionDecisionStatus.REJECTED
    assert "confidence_below_threshold" in rejected.reasons
    assert "expected_value_below_threshold" in rejected.reasons
    assert "risk_above_limit" in rejected.reasons

    hold_prediction = CanonicalPredictionFactory.create(
        engine_id="oracle.pattern",
        market_id="KX-HOLD",
        direction=PredictionDirection.HOLD,
        confidence=0.90,
        score=0.0,
        probability=0.50,
        expected_value=0.03,
        risk=0.10,
        features={},
        explanation=None,
    )

    hold = gateway.evaluate(hold_prediction)

    assert hold.status == ExecutionDecisionStatus.HOLD
    assert "hold_direction_not_executable" in hold.reasons

    assert len(gateway.list_decisions()) == 3
    assert gateway.latest_decision("KX-APPROVE") == approved

    health = gateway.health()
    assert health["status"] == "ok"
    assert health["decision_count"] == 3

    strict_gateway = create_qseries_execution_gateway(
        ExecutionRiskLimits(min_confidence=0.95)
    )

    strict_decision = strict_gateway.evaluate(approved_prediction)
    assert strict_decision.status == ExecutionDecisionStatus.REJECTED
    assert "confidence_below_threshold" in strict_decision.reasons

    print("[PASS] INT-004 Q Series Execution Gateway")
    print(health)


if __name__ == "__main__":
    test_int_004_qseries_execution_gateway()
