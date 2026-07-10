
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleIntelligenceEngineContract,
    OraclePredictionRequest,
)
from qseries_v2.integration.oracle_signal_bus import OracleSignalBus
from qseries_v2.integration.multi_engine_oracle_aggregator import MultiEngineOracleAggregator
from qseries_v2.integration.qseries_execution_gateway import QSeriesExecutionGateway


@dataclass(frozen=True)
class OracleOrchestrationResult:
    status: str
    market_id: str
    aggregate: Dict[str, Any]
    canonical_prediction: Dict[str, Any]
    execution_decision: Dict[str, Any]
    signal_count: int
    errors: List[str]
    generated_at: str

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleOrchestrator:
    """
    INT-008 Oracle Orchestrator.

    Single canonical coordinator for:

    Oracle engines
    -> Aggregator
    -> Canonical prediction
    -> Signal bus
    -> Q Series execution gateway

    This module does not place trades.
    """

    def __init__(
        self,
        signal_bus: Optional[OracleSignalBus] = None,
        aggregator: Optional[MultiEngineOracleAggregator] = None,
        execution_gateway: Optional[QSeriesExecutionGateway] = None,
    ) -> None:
        self.signal_bus = signal_bus or OracleSignalBus()
        self.aggregator = aggregator or MultiEngineOracleAggregator()
        self.execution_gateway = execution_gateway or QSeriesExecutionGateway()

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def register_engine(self, engine: OracleIntelligenceEngineContract) -> Dict[str, Any]:
        metadata = engine.metadata()

        if not metadata.oracle_read_only:
            return {
                "status": "error",
                "engine_id": metadata.engine_id,
                "reason": "oracle_engine_not_read_only",
            }

        self.aggregator.register_engine(engine)

        return {
            "status": "ok",
            "engine_id": metadata.engine_id,
            "engine_count": len(self.aggregator.engines),
        }

    def run_market(
        self,
        market_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> OracleOrchestrationResult:
        errors: List[str] = []

        if not market_id:
            return OracleOrchestrationResult(
                status="error",
                market_id="",
                aggregate={},
                canonical_prediction={},
                execution_decision={},
                signal_count=len(self.signal_bus.list_signals()),
                errors=["market_id_required"],
                generated_at=self.now_iso(),
            )

        request = OraclePredictionRequest.create(market_id, payload or {})

        aggregate = self.aggregator.aggregate(request)
        canonical = self.aggregator.to_canonical_prediction(aggregate)

        decision = self.execution_gateway.evaluate(canonical)

        signal_count_before = len(self.signal_bus.list_signals())

        # Emit a synthetic aggregate signal into the bus so the terminal/UI can stream it.
        from qseries_v2.integration.oracle_intelligence_interface_contract import OraclePredictionResult, OracleExplanation

        prediction_result = OraclePredictionResult(
            engine_id=canonical.identity.engine_id,
            market_id=canonical.identity.market_id,
            prediction=canonical.direction.value,
            confidence=canonical.metrics.confidence,
            score=canonical.metrics.score,
            features=canonical.features,
            generated_at=canonical.identity.generated_at,
        )

        explanation = None
        if canonical.explanation:
            explanation = OracleExplanation(
                engine_id=canonical.identity.engine_id,
                market_id=canonical.identity.market_id,
                summary=canonical.explanation.summary,
                reasons=canonical.explanation.reasons,
                evidence=canonical.explanation.evidence,
                generated_at=canonical.identity.generated_at,
            )

        self.signal_bus.emit(prediction_result, explanation)

        signal_count_after = len(self.signal_bus.list_signals())

        return OracleOrchestrationResult(
            status="ok" if not errors else "error",
            market_id=market_id,
            aggregate=aggregate.to_dict(),
            canonical_prediction=canonical.to_dict(),
            execution_decision=decision.to_dict(),
            signal_count=signal_count_after,
            errors=errors,
            generated_at=self.now_iso(),
        )

    def pipeline_status(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "orchestrator": "oracle_orchestrator",
            "engine_count": len(self.aggregator.engines),
            "signal_count": len(self.signal_bus.list_signals()),
            "decision_count": len(self.execution_gateway.list_decisions()),
            "aggregator": self.aggregator.health(),
            "signal_bus": self.signal_bus.health(),
            "execution_gateway": self.execution_gateway.health(),
        }

    def health(self) -> Dict[str, Any]:
        return self.pipeline_status()


def create_oracle_orchestrator(
    signal_bus: Optional[OracleSignalBus] = None,
    aggregator: Optional[MultiEngineOracleAggregator] = None,
    execution_gateway: Optional[QSeriesExecutionGateway] = None,
) -> OracleOrchestrator:
    return OracleOrchestrator(
        signal_bus=signal_bus,
        aggregator=aggregator,
        execution_gateway=execution_gateway,
    )


oracle_orchestrator = create_oracle_orchestrator


__all__ = [
    "OracleOrchestrationResult",
    "OracleOrchestrator",
    "create_oracle_orchestrator",
    "oracle_orchestrator",
]
