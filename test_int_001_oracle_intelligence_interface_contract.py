
from datetime import datetime, timezone
from typing import Any, Dict, List

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleEngineMetadata,
    OracleEngineCapability,
    OraclePredictionRequest,
    OraclePredictionResult,
    OracleExplanation,
    OracleEngineHealth,
    OracleIntelligenceEngineContract,
    OracleIntelligenceContractValidator,
)


class DummyOracleEngine:
    def metadata(self) -> OracleEngineMetadata:
        return OracleEngineMetadata(
            engine_id="oracle.dummy",
            name="Dummy Oracle Engine",
            version="1.0.0",
            description="Test engine",
        )

    def capabilities(self) -> List[OracleEngineCapability]:
        return [
            OracleEngineCapability(
                name="predict_market",
                description="Predicts market direction",
                inputs=["market_id", "payload"],
                outputs=["prediction", "confidence", "score"],
            )
        ]

    def schema(self) -> Dict[str, Any]:
        return {
            "request": ["market_id", "payload"],
            "response": ["prediction", "confidence", "score", "features"],
        }

    def health(self) -> OracleEngineHealth:
        return OracleEngineHealth(
            engine_id="oracle.dummy",
            status="ok",
            details={"ready": True},
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    def predict(self, request: OraclePredictionRequest) -> OraclePredictionResult:
        return OraclePredictionResult(
            engine_id="oracle.dummy",
            market_id=request.market_id,
            prediction="YES",
            confidence=0.75,
            score=0.18,
            features={"signal": "test"},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def explain(self, request: OraclePredictionRequest) -> OracleExplanation:
        return OracleExplanation(
            engine_id="oracle.dummy",
            market_id=request.market_id,
            summary="Dummy explanation",
            reasons=["Test reason"],
            evidence={"sample": True},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


class BrokenEngine:
    def metadata(self):
        return {}


def test_int_001_oracle_intelligence_interface_contract():
    engine = DummyOracleEngine()

    assert isinstance(engine, OracleIntelligenceEngineContract)

    validation = OracleIntelligenceContractValidator.validate(engine)
    assert validation["status"] == "ok"
    assert validation["missing_methods"] == []

    broken = OracleIntelligenceContractValidator.validate(BrokenEngine())
    assert broken["status"] == "error"
    assert "predict" in broken["missing_methods"]

    metadata = engine.metadata()
    assert metadata.engine_id == "oracle.dummy"
    assert metadata.oracle_read_only is True

    capabilities = engine.capabilities()
    assert len(capabilities) == 1
    assert capabilities[0].name == "predict_market"

    request = OraclePredictionRequest.create("KXTEST-001", {"price": 42})
    assert request.market_id == "KXTEST-001"

    prediction = engine.predict(request)
    assert prediction.market_id == "KXTEST-001"
    assert prediction.prediction == "YES"
    assert prediction.confidence == 0.75

    explanation = engine.explain(request)
    assert explanation.summary == "Dummy explanation"
    assert explanation.reasons == ["Test reason"]

    health = engine.health()
    assert health.ok is True

    print("[PASS] INT-001 Oracle Intelligence Interface Contract")
    print({
        "engine_id": metadata.engine_id,
        "contract_status": validation["status"],
        "capabilities": [item.to_dict() for item in capabilities],
    })


if __name__ == "__main__":
    test_int_001_oracle_intelligence_interface_contract()
