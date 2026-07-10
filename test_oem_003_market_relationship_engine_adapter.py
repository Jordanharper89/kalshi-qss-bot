from qseries_v2.integration.oem_003_market_relationship_engine_adapter import (
    ENGINE_ID,
    MarketRelationshipEngineAdapter,
    build_engine,
)


def test_oem_003_adapter_health():
    engine = build_engine()
    health = engine.health()

    assert health["engine_id"] == ENGINE_ID
    assert health["status"] == "ok"
    assert health["details"]["read_only"] is True


def test_oem_003_adapter_analyze_produces_signals():
    engine = MarketRelationshipEngineAdapter(
        engine=None
    )

    result = engine.analyze(
        {
            "market_id": "TEST-MARKET-YES",
            "related_market_id": "TEST-RELATED-NO",
            "relationship_score": 0.27,
            "confidence": 0.72,
        }
    )

    assert result.engine_id == ENGINE_ID
    assert result.status in {"ok", "degraded", "empty"}
    assert len(result.signals) == 1
    assert result.signals[0]["market_id"] == "TEST-MARKET-YES"
    assert result.signals[0]["related_market_id"] == "TEST-RELATED-NO"
    assert result.signals[0]["confidence"] == 0.72


def test_oem_003_adapter_predicts_canonical_predictions():
    engine = MarketRelationshipEngineAdapter(engine=None)

    predictions = engine.predict(
        {
            "market_id": "TEST-MARKET-YES",
            "related_market_id": "TEST-RELATED-NO",
            "relationship_score": 0.31,
            "confidence": 0.81,
        }
    )

    assert len(predictions) == 1

    prediction = predictions[0]

    if isinstance(prediction, dict):
        assert prediction["engine_id"] == ENGINE_ID
        assert prediction["market_id"] == "TEST-MARKET-YES"
        assert prediction["side"] == "YES"
        assert prediction["confidence"] == 0.81
    else:
        assert prediction.engine_id == ENGINE_ID
        assert prediction.market_id == "TEST-MARKET-YES"
        assert prediction.side == "YES"
        assert prediction.confidence == 0.81


def test_oem_003_runtime_registration_shape():
    class DummyRuntime:
        def __init__(self):
            self.engines = {}

        def register_engine(self, engine):
            self.engines[engine.engine_id] = engine

    runtime = DummyRuntime()
    engine = build_engine()

    runtime.register_engine(engine)

    assert ENGINE_ID in runtime.engines
    assert runtime.engines[ENGINE_ID].read_only is True


if __name__ == "__main__":
    test_oem_003_adapter_health()
    test_oem_003_adapter_analyze_produces_signals()
    test_oem_003_adapter_predicts_canonical_predictions()
    test_oem_003_runtime_registration_shape()

    engine = build_engine()
    result = engine.analyze(
        {
            "market_id": "TEST-MARKET-YES",
            "related_market_id": "TEST-RELATED-NO",
            "relationship_score": 0.27,
            "confidence": 0.72,
        }
    )
    predictions = engine.predict(
        {
            "market_id": "TEST-MARKET-YES",
            "related_market_id": "TEST-RELATED-NO",
            "relationship_score": 0.31,
            "confidence": 0.81,
        }
    )

    print("[PASS] OEM-003 Market Relationship Engine Adapter")
    print(
        {
            "engine_id": engine.engine_id,
            "health": engine.health()["status"],
            "signals": len(result.signals),
            "predictions": len(predictions),
            "read_only": engine.read_only,
        }
    )
