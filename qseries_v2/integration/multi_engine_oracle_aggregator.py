
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleIntelligenceEngineContract,
    OraclePredictionRequest,
    OraclePredictionResult,
    OracleExplanation,
)
from qseries_v2.integration.canonical_prediction_contract import (
    CanonicalPrediction,
    CanonicalPredictionFactory,
    PredictionDirection,
    PredictionExplanation,
)


@dataclass(frozen=True)
class AggregatedOracleSignal:
    market_id: str
    engine_count: int
    direction: str
    confidence: float
    score: float
    probability: float
    expected_value: float
    risk: float
    engine_results: List[Dict[str, Any]]
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MultiEngineOracleAggregator:
    """
    INT-006 Multi-Engine Oracle Aggregator.

    Combines multiple read-only Oracle engines into one canonical prediction.
    Does not execute trades.
    """

    def __init__(self, engines: List[OracleIntelligenceEngineContract] | None = None) -> None:
        self.engines = engines or []

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def register_engine(self, engine: OracleIntelligenceEngineContract) -> None:
        self.engines.append(engine)

    def aggregate(self, request: OraclePredictionRequest) -> AggregatedOracleSignal:
        if not self.engines:
            return AggregatedOracleSignal(
                market_id=request.market_id,
                engine_count=0,
                direction="HOLD",
                confidence=0.0,
                score=0.0,
                probability=0.5,
                expected_value=0.0,
                risk=1.0,
                engine_results=[],
                generated_at=self.now_iso(),
            )

        results: List[OraclePredictionResult] = []
        explanations: List[OracleExplanation] = []

        for engine in self.engines:
            health = engine.health()
            metadata = engine.metadata()

            if not health.ok:
                continue

            if not metadata.oracle_read_only:
                continue

            results.append(engine.predict(request))
            explanations.append(engine.explain(request))

        if not results:
            return AggregatedOracleSignal(
                market_id=request.market_id,
                engine_count=0,
                direction="HOLD",
                confidence=0.0,
                score=0.0,
                probability=0.5,
                expected_value=0.0,
                risk=1.0,
                engine_results=[],
                generated_at=self.now_iso(),
            )

        yes_votes = sum(1 for result in results if result.prediction.upper() == "YES")
        no_votes = sum(1 for result in results if result.prediction.upper() == "NO")

        if yes_votes > no_votes:
            direction = "YES"
        elif no_votes > yes_votes:
            direction = "NO"
        else:
            direction = "HOLD"

        avg_confidence = sum(float(result.confidence) for result in results) / len(results)
        avg_score = sum(float(result.score) for result in results) / len(results)

        probabilities = [
            float(result.features.get("probability", result.confidence))
            for result in results
        ]
        expected_values = [
            float(result.features.get("expected_value", result.score))
            for result in results
        ]
        risks = [
            float(result.features.get("risk", max(0.0, 1.0 - result.confidence)))
            for result in results
        ]

        return AggregatedOracleSignal(
            market_id=request.market_id,
            engine_count=len(results),
            direction=direction,
            confidence=float(avg_confidence),
            score=float(avg_score),
            probability=float(sum(probabilities) / len(probabilities)),
            expected_value=float(sum(expected_values) / len(expected_values)),
            risk=float(sum(risks) / len(risks)),
            engine_results=[result.to_dict() for result in results],
            generated_at=self.now_iso(),
        )

    def to_canonical_prediction(self, aggregate: AggregatedOracleSignal) -> CanonicalPrediction:
        direction = {
            "YES": PredictionDirection.YES,
            "NO": PredictionDirection.NO,
        }.get(aggregate.direction, PredictionDirection.HOLD)

        explanation = PredictionExplanation(
            summary=f"Consensus from {aggregate.engine_count} Oracle engines",
            reasons=[
                f"Consensus direction: {aggregate.direction}",
                f"Average confidence: {aggregate.confidence:.2f}",
                f"Average expected value: {aggregate.expected_value:.2f}",
            ],
            evidence={
                "engine_count": aggregate.engine_count,
                "engine_results": aggregate.engine_results,
            },
        )

        return CanonicalPredictionFactory.create(
            engine_id="oracle.multi_engine_aggregator",
            market_id=aggregate.market_id,
            direction=direction,
            confidence=aggregate.confidence,
            score=aggregate.score,
            probability=aggregate.probability,
            expected_value=aggregate.expected_value,
            risk=aggregate.risk,
            features={
                "engine_count": aggregate.engine_count,
                "source": "multi_engine_aggregator",
            },
            explanation=explanation,
        )

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "aggregator": "multi_engine_oracle_aggregator",
            "engine_count": len(self.engines),
        }


def create_multi_engine_oracle_aggregator(
    engines: List[OracleIntelligenceEngineContract] | None = None,
) -> MultiEngineOracleAggregator:
    return MultiEngineOracleAggregator(engines=engines)


multi_engine_oracle_aggregator = create_multi_engine_oracle_aggregator


__all__ = [
    "AggregatedOracleSignal",
    "MultiEngineOracleAggregator",
    "create_multi_engine_oracle_aggregator",
    "multi_engine_oracle_aggregator",
]
