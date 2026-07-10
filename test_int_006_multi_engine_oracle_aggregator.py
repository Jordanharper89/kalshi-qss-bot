
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
from qseries_v2.integration.canonical_prediction_contract import PredictionDirection
from qseries_v2.integration.multi_engine_oracle_aggregator import (
    MultiEngineOracleAggregator,
    create_multi_engine_oracle_aggregator,
    multi_engine_oracle_aggregator,
)


class DummyEngine:
    def __init__(self, engine_id: str, prediction: str, confidence: float, score: float):
        self.engine_id = engine_id
        self._prediction = prediction
        self._confidence = confidence
        self._score = score

    def metadata(self):
        return OracleEngineMetadata(
            engine_id=self.engine_id,
            name=self.engine_id,
            version="1.0.0",
            description="Dummy engine",
            oracle_read_only=True,
        )

    def capabilities(self):
        return [
            OracleEngineCapability(
                name="predict_market",
                description="test",
                inputs=["market_id"],
                outputs=["prediction"],
            )
        ]

    def schema(self):
        return {}

    def health(self):
        return OracleEngineHealth(
            engine_id=self.engine_id,
            status="ok",
            details={},
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    def predict(self, request):
        return OraclePredictionResult(
            engine_id=self.engine_id,
            market_id=request.market_id,
            prediction=self._prediction,
            confidence=self._confidence,
            score=self._score,
            features={
                "probability": self._confidence,
                "expected_value": self._score,
                "risk": 1.0 - self._confidence,
            },
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def explain(self, request):
        return OracleExplanation(
            engine_id=self.engine_id,
            market_id=request.market_id,
            summary=f"{self.engine_id} says {self._prediction}",
            reasons=["dummy"],
            evidence={},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


def test_int_006_multi_engine_oracle_aggregator():
    aggregator = create_multi_engine_oracle_aggregator()

    assert isinstance(aggregator, MultiEngineOracleAggregator)
    assert multi_engine_oracle_aggregator is create_multi_engine_oracle_aggregator

    empty = aggregator.aggregate(OraclePredictionRequest.create("KX-EMPTY"))
    assert empty.direction == "HOLD"
    assert empty.engine_count == 0

    aggregator.register_engine(DummyEngine("oracle.a", "YES", 0.8, 0.08))
    aggregator.register_engine(DummyEngine("oracle.b", "YES", 0.9, 0.12))
    aggregator.register_engine(DummyEngine("oracle.c", "NO", 0.7, 0.02))

    request = OraclePredictionRequest.create("KX-CONSENSUS")

    aggregate = aggregator.aggregate(request)

    assert aggregate.market_id == "KX-CONSENSUS"
    assert aggregate.engine_count == 3
    assert aggregate.direction == "YES"
    assert round(aggregate.confidence, 2) == 0.8

    canonical = aggregator.to_canonical_prediction(aggregate)

    assert canonical.identity.engine_id == "oracle.multi_engine_aggregator"
    assert canonical.identity.market_id == "KX-CONSENSUS"
    assert canonical.direction == PredictionDirection.YES
    assert canonical.features["engine_count"] == 3
    assert canonical.explanation is not None

    health = aggregator.health()
    assert health["status"] == "ok"
    assert health["engine_count"] == 3

    print("[PASS] INT-006 Multi-Engine Oracle Aggregator")
    print(aggregate.to_dict())


if __name__ == "__main__":
    test_int_006_multi_engine_oracle_aggregator()
