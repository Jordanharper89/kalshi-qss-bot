
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
