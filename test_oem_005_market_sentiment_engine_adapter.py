from qseries_v2.integration.oem_005_market_sentiment_engine_adapter import (
    ENGINE_ID,
    MarketSentimentEngineAdapter,
    build_engine,
)


def test_oem_005_adapter_health():
    engine = build_engine()
    health = engine.health()

    assert health["engine_id"] == ENGINE_ID
    assert health["status"] == "ok"
    assert health["details"]["read_only"] is True


def test_oem_005_adapter_analyze_produces_signals():
    engine = MarketSentimentEngineAdapter(engine=None)

    result = engine.analyze(
        {
            "market_id": "TEST-SENTIMENT-YES",
            "sentiment_source": "public_consensus",
            "sentiment_score": 0.38,
            "confidence": 0.79,
        }
    )

    assert result.engine_id == ENGINE_ID
    assert result.status in {"ok", "degraded", "empty"}
    assert len(result.signals) == 1
    assert result.signals[0]["market_id"] == "TEST-SENTIMENT-YES"
    assert result.signals[0]["sentiment_source"] == "public_consensus"
    assert result.signals[0]["sentiment_label"] == "bullish"
    assert result.signals[0]["confidence"] == 0.79


def test_oem_005_adapter_predicts_canonical_predictions():
    engine = MarketSentimentEngineAdapter(engine=None)

    predictions = engine.predict(
        {
            "market_id": "TEST-SENTIMENT-YES",
            "sentiment_source": "news_flow",
            "sentiment_score": 0.44,
            "confidence": 0.86,
        }
    )

    assert len(predictions) == 1
    prediction = predictions[0]

    if isinstance(prediction, dict):
        assert prediction["engine_id"] == ENGINE_ID
        assert prediction["market_id"] == "TEST-SENTIMENT-YES"
        assert prediction["side"] == "YES"
        assert prediction["confidence"] == 0.86
    else:
        assert prediction.engine_id == ENGINE_ID
        assert prediction.market_id == "TEST-SENTIMENT-YES"
        assert prediction.side == "YES"
        assert prediction.confidence == 0.86


def test_oem_005_negative_sentiment_maps_to_no():
    engine = MarketSentimentEngineAdapter(engine=None)

    predictions = engine.predict(
        {
            "market_id": "TEST-SENTIMENT-NO",
            "sentiment_score": -0.41,
            "confidence": 0.74,
        }
    )

    prediction = predictions[0]

    if isinstance(prediction, dict):
        assert prediction["side"] == "NO"
    else:
        assert prediction.side == "NO"


def test_oem_005_runtime_registration_shape():
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
    test_oem_005_adapter_health()
    test_oem_005_adapter_analyze_produces_signals()
    test_oem_005_adapter_predicts_canonical_predictions()
    test_oem_005_negative_sentiment_maps_to_no()
    test_oem_005_runtime_registration_shape()

    engine = build_engine()
    result = engine.analyze(
        {
            "market_id": "TEST-SENTIMENT-YES",
            "sentiment_source": "public_consensus",
            "sentiment_score": 0.38,
            "confidence": 0.79,
        }
    )
    predictions = engine.predict(
        {
            "market_id": "TEST-SENTIMENT-YES",
            "sentiment_source": "news_flow",
            "sentiment_score": 0.44,
            "confidence": 0.86,
        }
    )

    print("[PASS] OEM-005 Market Sentiment Engine Adapter")
    print(
        {
            "engine_id": engine.engine_id,
            "health": engine.health()["status"],
            "signals": len(result.signals),
            "predictions": len(predictions),
            "read_only": engine.read_only,
        }
    )
