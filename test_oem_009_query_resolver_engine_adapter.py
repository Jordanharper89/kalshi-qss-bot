from qseries_v2.integration.oem_009_query_resolver_engine_adapter import (
    ENGINE_ID,
    QueryResolverEngineAdapter,
    build_engine,
)


def test_oem_009_adapter_health():
    engine = build_engine()
    health = engine.health()

    assert health["engine_id"] == ENGINE_ID
    assert health["status"] == "ok"
    assert health["details"]["read_only"] is True


def test_oem_009_adapter_analyze_produces_signals():
    engine = QueryResolverEngineAdapter(engine=None)

    result = engine.analyze(
        {
            "query": "Will BTC close above 70000?",
            "market_id": "TEST-RESOLVER-YES",
            "resolved_market_id": "TEST-RESOLVER-YES",
            "adapter_id": "adp.kalshi",
            "resolver_type": "exact_market_match",
            "resolver_score": 0.44,
            "confidence": 0.84,
        }
    )

    assert result.engine_id == ENGINE_ID
    assert result.status in {"ok", "degraded", "empty"}
    assert len(result.signals) == 1
    assert result.signals[0]["market_id"] == "TEST-RESOLVER-YES"
    assert result.signals[0]["resolved_market_id"] == "TEST-RESOLVER-YES"
    assert result.signals[0]["adapter_id"] == "adp.kalshi"
    assert result.signals[0]["confidence"] == 0.84


def test_oem_009_adapter_predicts_canonical_predictions():
    engine = QueryResolverEngineAdapter(engine=None)

    predictions = engine.predict(
        {
            "query": "Will ETH close above 4000?",
            "market_id": "TEST-RESOLVER-YES",
            "resolved_market_id": "TEST-RESOLVER-YES",
            "resolver_score": 0.51,
            "confidence": 0.89,
        }
    )

    assert len(predictions) == 1
    prediction = predictions[0]

    if isinstance(prediction, dict):
        assert prediction["engine_id"] == ENGINE_ID
        assert prediction["market_id"] == "TEST-RESOLVER-YES"
        assert prediction["side"] == "YES"
        assert prediction["confidence"] == 0.89
    else:
        assert prediction.engine_id == ENGINE_ID
        assert prediction.market_id == "TEST-RESOLVER-YES"
        assert prediction.side == "YES"
        assert prediction.confidence == 0.89


def test_oem_009_negative_resolver_maps_to_no():
    engine = QueryResolverEngineAdapter(engine=None)

    predictions = engine.predict(
        {
            "market_id": "TEST-RESOLVER-NO",
            "resolver_score": -0.31,
            "confidence": 0.72,
        }
    )

    prediction = predictions[0]

    if isinstance(prediction, dict):
        assert prediction["side"] == "NO"
    else:
        assert prediction.side == "NO"


def test_oem_009_runtime_registration_shape():
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
    test_oem_009_adapter_health()
    test_oem_009_adapter_analyze_produces_signals()
    test_oem_009_adapter_predicts_canonical_predictions()
    test_oem_009_negative_resolver_maps_to_no()
    test_oem_009_runtime_registration_shape()

    engine = build_engine()
    result = engine.analyze(
        {
            "query": "Will BTC close above 70000?",
            "market_id": "TEST-RESOLVER-YES",
            "resolved_market_id": "TEST-RESOLVER-YES",
            "adapter_id": "adp.kalshi",
            "resolver_type": "exact_market_match",
            "resolver_score": 0.44,
            "confidence": 0.84,
        }
    )
    predictions = engine.predict(
        {
            "query": "Will ETH close above 4000?",
            "market_id": "TEST-RESOLVER-YES",
            "resolved_market_id": "TEST-RESOLVER-YES",
            "resolver_score": 0.51,
            "confidence": 0.89,
        }
    )

    print("[PASS] OEM-009 Query Resolver Engine Adapter")
    print(
        {
            "engine_id": engine.engine_id,
            "health": engine.health()["status"],
            "signals": len(result.signals),
            "predictions": len(predictions),
            "read_only": engine.read_only,
        }
    )
