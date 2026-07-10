
from datetime import datetime, timezone

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleEngineMetadata,
    OracleEngineCapability,
    OraclePredictionResult,
    OraclePredictionRequest,
    OracleExplanation,
    OracleEngineHealth,
)
from qseries_v2.integration.oracle_engine_registry import (
    OracleEngineRegistry,
    create_oracle_engine_registry,
    oracle_engine_registry,
)


class RegistryDummyEngine:
    def metadata(self):
        return OracleEngineMetadata(
            engine_id="oracle.registry.test",
            name="Registry Test Engine",
            version="1.0.0",
            description="Registry test engine",
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
            engine_id="oracle.registry.test",
            status="ok",
            details={"ready": True},
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    def predict(self, request):
        return OraclePredictionResult(
            engine_id="oracle.registry.test",
            market_id=request.market_id,
            prediction="YES",
            confidence=0.80,
            score=0.08,
            features={},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def explain(self, request):
        return OracleExplanation(
            engine_id="oracle.registry.test",
            market_id=request.market_id,
            summary="Registry test explanation",
            reasons=["test"],
            evidence={},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


class UnsafeEngine(RegistryDummyEngine):
    def metadata(self):
        return OracleEngineMetadata(
            engine_id="oracle.unsafe",
            name="Unsafe Engine",
            version="1.0.0",
            description="Unsafe",
            oracle_read_only=False,
        )


def test_int_009_oracle_engine_registry():
    registry = create_oracle_engine_registry()

    assert isinstance(registry, OracleEngineRegistry)
    assert oracle_engine_registry is create_oracle_engine_registry

    entry = registry.register(RegistryDummyEngine())

    assert entry.engine_id == "oracle.registry.test"
    assert registry.count() == 1
    assert registry.get_engine("oracle.registry.test") is not None
    assert registry.get_entry("oracle.registry.test") == entry
    assert len(registry.list_entries()) == 1
    assert len(registry.list_engines()) == 1

    health_map = registry.refresh_health()
    assert health_map["oracle.registry.test"]["status"] == "ok"

    health = registry.health()
    assert health["status"] == "ok"
    assert health["engine_count"] == 1

    try:
        registry.register(UnsafeEngine())
        assert False, "unsafe engine should fail"
    except ValueError as exc:
        assert "read-only" in str(exc)

    assert registry.unregister("oracle.registry.test") is True
    assert registry.count() == 0
    assert registry.unregister("missing") is False

    print("[PASS] INT-009 Oracle Engine Registry")
    print(health)


if __name__ == "__main__":
    test_int_009_oracle_engine_registry()
