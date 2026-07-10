from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "integration" / "oracle_to_qseries_integration_gate.py"
TEST = ROOT / "test_int_005_oracle_to_qseries_integration_gate.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleIntelligenceEngineContract,
    OracleIntelligenceContractValidator,
    OraclePredictionRequest,
)
from qseries_v2.integration.oracle_signal_bus import OracleSignalBus, OracleSignal
from qseries_v2.integration.canonical_prediction_contract import (
    CanonicalPrediction,
    CanonicalPredictionFactory,
    PredictionDirection,
    PredictionExplanation,
)
from qseries_v2.integration.qseries_execution_gateway import (
    QSeriesExecutionGateway,
    ExecutionDecision,
)


@dataclass(frozen=True)
class OracleToQSeriesIntegrationResult:
    status: str
    market_id: str
    engine_id: str
    signal: Dict[str, Any]
    canonical_prediction: Dict[str, Any]
    execution_decision: Dict[str, Any]
    errors: List[str]
    generated_at: str

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleToQSeriesIntegrationGate:
    """
    INT-005 End-to-End Oracle -> Q Series Integration Gate.

    Flow:
        Oracle Engine Contract
        -> Oracle Signal Bus
        -> Canonical Prediction Contract
        -> Q Series Execution Gateway

    This gate does NOT place trades.
    It verifies that intelligence can safely become an execution decision.
    """

    def __init__(
        self,
        signal_bus: Optional[OracleSignalBus] = None,
        execution_gateway: Optional[QSeriesExecutionGateway] = None,
    ) -> None:
        self.signal_bus = signal_bus or OracleSignalBus()
        self.execution_gateway = execution_gateway or QSeriesExecutionGateway()

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def run(
        self,
        engine: OracleIntelligenceEngineContract,
        request: OraclePredictionRequest,
    ) -> OracleToQSeriesIntegrationResult:
        errors: List[str] = []

        validation = OracleIntelligenceContractValidator.validate(engine)
        if validation["status"] != "ok":
            errors.extend([f"missing_method:{name}" for name in validation["missing_methods"]])

        metadata = engine.metadata()
        if not metadata.oracle_read_only:
            errors.append("oracle_engine_not_read_only")

        health = engine.health()
        if not health.ok:
            errors.append("oracle_engine_health_not_ok")

        prediction = engine.predict(request)
        explanation = engine.explain(request)

        signal = self.signal_bus.emit(prediction, explanation)

        canonical = self.signal_to_canonical_prediction(signal)

        decision = self.execution_gateway.evaluate(canonical)

        status = "ok" if not errors else "error"

        return OracleToQSeriesIntegrationResult(
            status=status,
            market_id=request.market_id,
            engine_id=metadata.engine_id,
            signal=signal.to_dict(),
            canonical_prediction=canonical.to_dict(),
            execution_decision=decision.to_dict(),
            errors=errors,
            generated_at=self.now_iso(),
        )

    def signal_to_canonical_prediction(self, signal: OracleSignal) -> CanonicalPrediction:
        direction = self.normalize_direction(signal.prediction)

        explanation = None
        if signal.explanation:
            explanation = PredictionExplanation(
                summary=signal.explanation.get("summary", ""),
                reasons=list(signal.explanation.get("reasons", [])),
                evidence=dict(signal.explanation.get("evidence", {})),
            )

        probability = float(signal.features.get("probability", signal.confidence))
        expected_value = float(signal.features.get("expected_value", signal.score))
        risk = float(signal.features.get("risk", max(0.0, 1.0 - signal.confidence)))

        return CanonicalPredictionFactory.create(
            engine_id=signal.engine_id,
            market_id=signal.market_id,
            direction=direction,
            confidence=signal.confidence,
            score=signal.score,
            probability=probability,
            expected_value=expected_value,
            risk=risk,
            features=signal.features,
            explanation=explanation,
        )

    @staticmethod
    def normalize_direction(value: str) -> PredictionDirection:
        upper = str(value).strip().upper()

        if upper == "YES":
            return PredictionDirection.YES

        if upper == "NO":
            return PredictionDirection.NO

        return PredictionDirection.HOLD

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "gate": "oracle_to_qseries_integration_gate",
            "signal_bus": self.signal_bus.health(),
            "execution_gateway": self.execution_gateway.health(),
        }


def create_oracle_to_qseries_integration_gate(
    signal_bus: Optional[OracleSignalBus] = None,
    execution_gateway: Optional[QSeriesExecutionGateway] = None,
) -> OracleToQSeriesIntegrationGate:
    return OracleToQSeriesIntegrationGate(
        signal_bus=signal_bus,
        execution_gateway=execution_gateway,
    )


oracle_to_qseries_integration_gate = create_oracle_to_qseries_integration_gate


__all__ = [
    "OracleToQSeriesIntegrationResult",
    "OracleToQSeriesIntegrationGate",
    "create_oracle_to_qseries_integration_gate",
    "oracle_to_qseries_integration_gate",
]
'''

test_code = r'''
from datetime import datetime, timezone
from typing import Any, Dict, List

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleEngineMetadata,
    OracleEngineCapability,
    OraclePredictionRequest,
    OraclePredictionResult,
    OracleExplanation,
    OracleEngineHealth,
)
from qseries_v2.integration.qseries_execution_gateway import ExecutionDecisionStatus
from qseries_v2.integration.oracle_to_qseries_integration_gate import (
    OracleToQSeriesIntegrationGate,
    create_oracle_to_qseries_integration_gate,
    oracle_to_qseries_integration_gate,
)


class PassingOracleEngine:
    def metadata(self) -> OracleEngineMetadata:
        return OracleEngineMetadata(
            engine_id="oracle.integration.test",
            name="Integration Test Oracle",
            version="1.0.0",
            description="End-to-end test oracle",
            oracle_read_only=True,
        )

    def capabilities(self) -> List[OracleEngineCapability]:
        return [
            OracleEngineCapability(
                name="predict_market",
                description="Predicts market direction",
                inputs=["market_id"],
                outputs=["prediction", "confidence", "score"],
            )
        ]

    def schema(self) -> Dict[str, Any]:
        return {
            "request": ["market_id", "payload"],
            "response": ["prediction", "confidence", "score"],
        }

    def health(self) -> OracleEngineHealth:
        return OracleEngineHealth(
            engine_id="oracle.integration.test",
            status="ok",
            details={"ready": True},
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    def predict(self, request: OraclePredictionRequest) -> OraclePredictionResult:
        return OraclePredictionResult(
            engine_id="oracle.integration.test",
            market_id=request.market_id,
            prediction="YES",
            confidence=0.84,
            score=0.09,
            features={
                "probability": 0.72,
                "expected_value": 0.07,
                "risk": 0.22,
                "source": "test",
            },
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def explain(self, request: OraclePredictionRequest) -> OracleExplanation:
        return OracleExplanation(
            engine_id="oracle.integration.test",
            market_id=request.market_id,
            summary="Approved integration signal",
            reasons=["High confidence", "Positive expected value"],
            evidence={"sample_count": 10},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


class UnsafeOracleEngine(PassingOracleEngine):
    def metadata(self) -> OracleEngineMetadata:
        return OracleEngineMetadata(
            engine_id="oracle.unsafe",
            name="Unsafe Oracle",
            version="1.0.0",
            description="Should fail read-only check",
            oracle_read_only=False,
        )


def test_int_005_oracle_to_qseries_integration_gate():
    gate = create_oracle_to_qseries_integration_gate()

    assert isinstance(gate, OracleToQSeriesIntegrationGate)
    assert oracle_to_qseries_integration_gate is create_oracle_to_qseries_integration_gate

    request = OraclePredictionRequest.create("KX-INTEGRATION-001", {"price": 42})

    result = gate.run(PassingOracleEngine(), request)

    assert result.status == "ok"
    assert result.ok is True
    assert result.market_id == "KX-INTEGRATION-001"
    assert result.engine_id == "oracle.integration.test"
    assert result.errors == []

    assert result.signal["market_id"] == "KX-INTEGRATION-001"
    assert result.canonical_prediction["direction"] == "YES"
    assert result.execution_decision["status"] == ExecutionDecisionStatus.APPROVED.value

    assert gate.signal_bus.latest_signal("KX-INTEGRATION-001") is not None
    assert gate.execution_gateway.latest_decision("KX-INTEGRATION-001") is not None

    unsafe = gate.run(UnsafeOracleEngine(), request)

    assert unsafe.status == "error"
    assert "oracle_engine_not_read_only" in unsafe.errors

    health = gate.health()
    assert health["status"] == "ok"

    print("[PASS] INT-005 Oracle To Q Series Integration Gate")
    print(result.to_dict())


if __name__ == "__main__":
    test_int_005_oracle_to_qseries_integration_gate()
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "integration" / "__init__.py"
existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .oracle_to_qseries_integration_gate import "
    "OracleToQSeriesIntegrationResult, OracleToQSeriesIntegrationGate, "
    "create_oracle_to_qseries_integration_gate, oracle_to_qseries_integration_gate\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" INT-005 INSTALLER")
print(" Oracle To Q Series Integration Gate")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] INT-005 installed")
print("")
print("Run:")
print("py test_int_005_oracle_to_qseries_integration_gate.py")