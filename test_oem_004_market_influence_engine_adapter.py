from qseries_v2.integration.oem_004_market_influence_engine_adapter import (
    ENGINE_ID,
    MarketInfluenceEngineAdapter,
    build_engine,
)


def test_oem_004_adapter_health():
    engine = build_engine()
    health = engine.health()

    assert health["engine_id"] == ENGINE_ID
    assert health["status"] == "ok"
    assert health["details"]["read_only"] is True


def test_oem_004_adapter_analyze_produces_signals():
    engine = MarketInfluenceEngineAdapter(engine=None)

    result = engine.analyze(
        {
            "market_id": "TEST-INFLUENCE-YES",
            "influence_source": "news_momentum",
            "influence_score": 0.34,
            "confidence": 0.76,
        }
    )

    assert result.engine_id == ENGINE_ID
    assert result.status in {"ok", "degraded", "empty"}
    assert len(result.signals) == 1
    assert result.signals[0]["market_id"] == "TEST-INFLUENCE-YES"
    assert result.signals[0]["influence_source"] == "news_momentum"
    assert result.signals[0]["confidence"] == 0.76


def test_oem_004_adapter_predicts_canonical_predictions():
    engine = MarketInfluenceEngineAdapter(engine=None)

    predictions = engine.predict(
        {
            "market_id": "TEST-INFLUENCE-YES",
            "influence_source": "liquidity_shift",
            "influence_score": 0.42,
            "confidence": 0.84,
        }
    )

    assert len(predictions) == 1
    prediction = predictions[0]

    if isinstance(prediction, dict):
        assert prediction["engine_id"] == ENGINE_ID
        assert prediction["market_id"] == "TEST-INFLUENCE-YES"
        assert prediction["side"] == "YES"
        assert prediction["confidence"] == 0.84
    else:
        assert prediction.engine_id == ENGINE_ID
        assert prediction.market_id == "TEST-INFLUENCE-YES"
        assert prediction.side == "YES"
        assert prediction.confidence == 0.84


def test_oem_004_runtime_registration_shape():
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
    test_oem_004_adapter_health()
    test_oem_004_adapter_analyze_produces_signals()
    test_oem_004_adapter_predicts_canonical_predictions()
    test_oem_004_runtime_registration_shape()

    engine = build_engine()
    result = engine.analyze(
        {
            "market_id": "TEST-INFLUENCE-YES",
            "influence_source": "news_momentum",
            "influence_score": 0.34,
            "confidence": 0.76,
        }
    )
    predictions = engine.predict(
        {
            "market_id": "TEST-INFLUENCE-YES",
            "influence_source": "liquidity_shift",
            "influence_score": 0.42,
            "confidence": 0.84,
        }
    )

    print("[PASS] OEM-004 Market Influence Engine Adapter")
    print(
        {
            "engine_id": engine.engine_id,
            "health": engine.health()["status"],
            "signals": len(result.signals),
            "predictions": len(predictions),
            "read_only": engine.read_only,
        }
    )
