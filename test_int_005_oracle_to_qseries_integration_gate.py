
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
