
from datetime import datetime, timezone

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleEngineMetadata,
    OracleEngineCapability,
    OraclePredictionResult,
    OracleExplanation,
    OracleEngineHealth,
)
from qseries_v2.integration.oracle_orchestrator import (
    OracleOrchestrator,
    create_oracle_orchestrator,
    oracle_orchestrator,
)


class OrchestratorDummyEngine:
    def metadata(self):
        return OracleEngineMetadata(
            engine_id="oracle.orchestrator.test",
            name="Orchestrator Test Engine",
            version="1.0.0",
            description="Orchestrator test engine",
            oracle_read_only=True,
        )

    def capabilities(self):
        return [
            OracleEngineCapability(
                name="predict_market",
                description="Predict market",
                inputs=["market_id"],
                outputs=["prediction"],
            )
        ]

    def schema(self):
        return {"request": ["market_id"], "response": ["prediction"]}

    def health(self):
        return OracleEngineHealth(
            engine_id="oracle.orchestrator.test",
            status="ok",
            details={"ready": True},
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    def predict(self, request):
        return OraclePredictionResult(
            engine_id="oracle.orchestrator.test",
            market_id=request.market_id,
            prediction="YES",
            confidence=0.89,
            score=0.11,
            features={
                "probability": 0.76,
                "expected_value": 0.09,
                "risk": 0.18,
            },
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def explain(self, request):
        return OracleExplanation(
            engine_id="oracle.orchestrator.test",
            market_id=request.market_id,
            summary="Orchestrator test signal",
            reasons=["Consensus ready", "Execution approved"],
            evidence={"sample_count": 15},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


class UnsafeEngine(OrchestratorDummyEngine):
    def metadata(self):
        return OracleEngineMetadata(
            engine_id="oracle.unsafe",
            name="Unsafe Engine",
            version="1.0.0",
            description="Unsafe",
            oracle_read_only=False,
        )


def test_int_008_oracle_orchestrator():
    orchestrator = create_oracle_orchestrator()

    assert isinstance(orchestrator, OracleOrchestrator)
    assert oracle_orchestrator is create_oracle_orchestrator

    rejected = orchestrator.register_engine(UnsafeEngine())
    assert rejected["status"] == "error"
    assert rejected["reason"] == "oracle_engine_not_read_only"

    registered = orchestrator.register_engine(OrchestratorDummyEngine())
    assert registered["status"] == "ok"
    assert registered["engine_count"] == 1

    missing = orchestrator.run_market("")
    assert missing.status == "error"
    assert "market_id_required" in missing.errors

    result = orchestrator.run_market("KX-ORCH-001", {"price": 42})

    assert result.ok is True
    assert result.market_id == "KX-ORCH-001"
    assert result.aggregate["direction"] == "YES"
    assert result.canonical_prediction["direction"] == "YES"
    assert result.execution_decision["status"] == "APPROVED"
    assert result.signal_count == 1

    status = orchestrator.pipeline_status()
    assert status["status"] == "ok"
    assert status["engine_count"] == 1
    assert status["signal_count"] == 1
    assert status["decision_count"] == 1

    print("[PASS] INT-008 Oracle Orchestrator")
    print(result.to_dict())


if __name__ == "__main__":
    test_int_008_oracle_orchestrator()
