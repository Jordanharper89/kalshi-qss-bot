
from datetime import datetime, timezone

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleEngineMetadata,
    OracleEngineCapability,
    OraclePredictionResult,
    OracleExplanation,
    OracleEngineHealth,
)
from qseries_v2.integration.oracle_intelligence_runtime import (
    OracleIntelligenceRuntime,
    create_oracle_intelligence_runtime,
    oracle_intelligence_runtime,
)


class RuntimeDummyEngine:
    def metadata(self):
        return OracleEngineMetadata(
            engine_id="oracle.runtime.test",
            name="Runtime Test Engine",
            version="1.0.0",
            description="Runtime test engine",
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
            engine_id="oracle.runtime.test",
            status="ok",
            details={"ready": True},
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    def predict(self, request):
        return OraclePredictionResult(
            engine_id="oracle.runtime.test",
            market_id=request.market_id,
            prediction="YES",
            confidence=0.91,
            score=0.13,
            features={
                "probability": 0.78,
                "expected_value": 0.10,
                "risk": 0.16,
            },
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def explain(self, request):
        return OracleExplanation(
            engine_id="oracle.runtime.test",
            market_id=request.market_id,
            summary="Runtime test signal",
            reasons=["Runtime healthy", "Consensus approved"],
            evidence={"sample_count": 20},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


class UnsafeRuntimeEngine(RuntimeDummyEngine):
    def metadata(self):
        return OracleEngineMetadata(
            engine_id="oracle.runtime.unsafe",
            name="Unsafe Runtime Engine",
            version="1.0.0",
            description="Unsafe runtime test engine",
            oracle_read_only=False,
        )


def test_int_010_oracle_intelligence_runtime():
    runtime = create_oracle_intelligence_runtime()

    assert isinstance(runtime, OracleIntelligenceRuntime)
    assert oracle_intelligence_runtime is create_oracle_intelligence_runtime

    health_before = runtime.health()
    assert health_before.status == "stopped"
    assert health_before.payload["started"] is False

    blocked = runtime.run_market("KX-RUNTIME-001")
    assert blocked.status == "error"
    assert "runtime_not_started" in blocked.errors

    unsafe = runtime.register_engine(UnsafeRuntimeEngine())
    assert unsafe.status == "error"

    registered = runtime.register_engine(RuntimeDummyEngine())
    assert registered.status == "ok"
    assert registered.payload["engine_count"] == 1

    engines = runtime.engines()
    assert engines.status == "ok"
    assert engines.payload["engine_count"] == 1

    started = runtime.start()
    assert started.status == "ok"
    assert started.payload["started"] is True

    run = runtime.run_market("KX-RUNTIME-001", {"price": 42})
    assert run.status == "ok"
    assert run.payload["market_id"] == "KX-RUNTIME-001"
    assert run.payload["execution_decision"]["status"] == "APPROVED"

    prediction = runtime.predict("KX-RUNTIME-002")
    assert prediction.status == "ok"
    assert prediction.payload["canonical_prediction"]["direction"] == "YES"

    decision = runtime.decision("KX-RUNTIME-003")
    assert decision.status == "ok"
    assert decision.payload["execution_decision"]["status"] == "APPROVED"

    explanation = runtime.explain("KX-RUNTIME-004")
    assert explanation.status == "ok"
    assert explanation.payload["explanation"]["summary"] == "Consensus from 1 Oracle engines"

    pipeline = runtime.pipeline_status()
    assert pipeline.status == "ok"
    assert pipeline.payload["started"] is True
    assert pipeline.payload["registry"]["engine_count"] == 1

    health_after = runtime.health()
    assert health_after.status == "ok"
    assert health_after.payload["engine_count"] == 1
    assert health_after.payload["decision_count"] >= 2

    stopped = runtime.stop()
    assert stopped.status == "ok"
    assert stopped.payload["started"] is False

    print("[PASS] INT-010 Oracle Intelligence Runtime")
    print(run.to_dict())


if __name__ == "__main__":
    test_int_010_oracle_intelligence_runtime()
