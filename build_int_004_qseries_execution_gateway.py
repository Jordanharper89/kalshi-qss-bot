from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "integration" / "qseries_execution_gateway.py"
TEST = ROOT / "test_int_004_qseries_execution_gateway.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

from qseries_v2.integration.canonical_prediction_contract import (
    CanonicalPrediction,
    PredictionDirection,
    CanonicalPredictionValidator,
)


class ExecutionDecisionStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    HOLD = "HOLD"


@dataclass(frozen=True)
class ExecutionRiskLimits:
    min_confidence: float = 0.70
    min_expected_value: float = 0.01
    max_risk: float = 0.35
    allow_hold: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExecutionDecision:
    decision_id: str
    market_id: str
    engine_id: str
    direction: str
    status: ExecutionDecisionStatus
    reasons: List[str]
    prediction: Dict[str, Any]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "market_id": self.market_id,
            "engine_id": self.engine_id,
            "direction": self.direction,
            "status": self.status.value,
            "reasons": list(self.reasons),
            "prediction": dict(self.prediction),
            "created_at": self.created_at,
        }


class QSeriesExecutionGateway:
    """
    INT-004 Q Series Execution Gateway.

    Converts canonical Oracle predictions into Q Series execution decisions.

    This module does NOT place trades.
    It only approves/rejects/holds based on canonical rules.
    """

    def __init__(self, risk_limits: ExecutionRiskLimits | None = None) -> None:
        self.risk_limits = risk_limits or ExecutionRiskLimits()
        self._decisions: List[ExecutionDecision] = []

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def evaluate(self, prediction: CanonicalPrediction) -> ExecutionDecision:
        validation = CanonicalPredictionValidator.validate(prediction)

        reasons: List[str] = []

        if validation["status"] != "ok":
            reasons.append(f"invalid_prediction:{','.join(validation['errors'])}")

        if prediction.direction == PredictionDirection.HOLD and not self.risk_limits.allow_hold:
            reasons.append("hold_direction_not_executable")

        if prediction.metrics.confidence < self.risk_limits.min_confidence:
            reasons.append("confidence_below_threshold")

        if prediction.metrics.expected_value < self.risk_limits.min_expected_value:
            reasons.append("expected_value_below_threshold")

        if prediction.metrics.risk > self.risk_limits.max_risk:
            reasons.append("risk_above_limit")

        if prediction.direction == PredictionDirection.HOLD:
            status = ExecutionDecisionStatus.HOLD
        elif reasons:
            status = ExecutionDecisionStatus.REJECTED
        else:
            status = ExecutionDecisionStatus.APPROVED

        decision = ExecutionDecision(
            decision_id=f"decision:{prediction.identity.engine_id}:{prediction.identity.market_id}:{len(self._decisions) + 1}",
            market_id=prediction.identity.market_id,
            engine_id=prediction.identity.engine_id,
            direction=prediction.direction.value,
            status=status,
            reasons=reasons,
            prediction=prediction.to_dict(),
            created_at=self.now_iso(),
        )

        self._decisions.append(decision)
        return decision

    def list_decisions(self, market_id: str | None = None) -> List[ExecutionDecision]:
        if market_id is None:
            return list(self._decisions)
        return [decision for decision in self._decisions if decision.market_id == market_id]

    def latest_decision(self, market_id: str) -> ExecutionDecision | None:
        matches = self.list_decisions(market_id)
        return matches[-1] if matches else None

    def clear(self) -> int:
        count = len(self._decisions)
        self._decisions.clear()
        return count

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "gateway": "qseries_execution_gateway",
            "decision_count": len(self._decisions),
            "risk_limits": self.risk_limits.to_dict(),
        }


def create_qseries_execution_gateway(
    risk_limits: ExecutionRiskLimits | None = None,
) -> QSeriesExecutionGateway:
    return QSeriesExecutionGateway(risk_limits=risk_limits)


qseries_execution_gateway = create_qseries_execution_gateway


__all__ = [
    "ExecutionDecisionStatus",
    "ExecutionRiskLimits",
    "ExecutionDecision",
    "QSeriesExecutionGateway",
    "create_qseries_execution_gateway",
    "qseries_execution_gateway",
]
'''

test_code = r'''
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
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "integration" / "__init__.py"
existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .qseries_execution_gateway import "
    "ExecutionDecisionStatus, ExecutionRiskLimits, ExecutionDecision, "
    "QSeriesExecutionGateway, create_qseries_execution_gateway, "
    "qseries_execution_gateway\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" INT-004 INSTALLER")
print(" Q Series Execution Gateway")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] INT-004 installed")
print("")
print("Run:")
print("py test_int_004_qseries_execution_gateway.py")