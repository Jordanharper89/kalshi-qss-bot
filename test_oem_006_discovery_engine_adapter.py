from qseries_v2.integration.oem_006_discovery_engine_adapter import (
    ENGINE_ID,
    DiscoveryEngineAdapter,
    build_engine,
)


def test_oem_006_adapter_health():
    engine = build_engine()
    health = engine.health()

    assert health["engine_id"] == ENGINE_ID
    assert health["status"] == "ok"
    assert health["details"]["read_only"] is True


def test_oem_006_adapter_analyze_produces_signals():
    engine = DiscoveryEngineAdapter(engine=None)

    result = engine.analyze(
        {
            "market_id": "TEST-DISCOVERY-YES",
            "discovery_source": "market_scan",
            "discovery_type": "emerging_market",
            "discovery_score": 0.36,
            "confidence": 0.78,
        }
    )

    assert result.engine_id == ENGINE_ID
    assert result.status in {"ok", "degraded", "empty"}
    assert len(result.signals) == 1
    assert result.signals[0]["market_id"] == "TEST-DISCOVERY-YES"
    assert result.signals[0]["discovery_source"] == "market_scan"
    assert result.signals[0]["discovery_type"] == "emerging_market"
    assert result.signals[0]["confidence"] == 0.78


def test_oem_006_adapter_predicts_canonical_predictions():
    engine = DiscoveryEngineAdapter(engine=None)

    predictions = engine.predict(
        {
            "market_id": "TEST-DISCOVERY-YES",
            "discovery_source": "market_scan",
            "discovery_type": "emerging_market",
            "discovery_score": 0.43,
            "confidence": 0.85,
        }
    )

    assert len(predictions) == 1
    prediction = predictions[0]

    if isinstance(prediction, dict):
        assert prediction["engine_id"] == ENGINE_ID
        assert prediction["market_id"] == "TEST-DISCOVERY-YES"
        assert prediction["side"] == "YES"
        assert prediction["confidence"] == 0.85
    else:
        assert prediction.engine_id == ENGINE_ID
        assert prediction.market_id == "TEST-DISCOVERY-YES"
        assert prediction.side == "YES"
        assert prediction.confidence == 0.85


def test_oem_006_negative_discovery_maps_to_no():
    engine = DiscoveryEngineAdapter(engine=None)

    predictions = engine.predict(
        {
            "market_id": "TEST-DISCOVERY-NO",
            "discovery_score": -0.29,
            "confidence": 0.71,
        }
    )

    prediction = predictions[0]

    if isinstance(prediction, dict):
        assert prediction["side"] == "NO"
    else:
        assert prediction.side == "NO"


def test_oem_006_runtime_registration_shape():
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
    test_oem_006_adapter_health()
    test_oem_006_adapter_analyze_produces_signals()
    test_oem_006_adapter_predicts_canonical_predictions()
    test_oem_006_negative_discovery_maps_to_no()
    test_oem_006_runtime_registration_shape()

    engine = build_engine()
    result = engine.analyze(
        {
            "market_id": "TEST-DISCOVERY-YES",
            "discovery_source": "market_scan",
            "discovery_type": "emerging_market",
            "discovery_score": 0.36,
            "confidence": 0.78,
        }
    )
    predictions = engine.predict(
        {
            "market_id": "TEST-DISCOVERY-YES",
            "discovery_source": "market_scan",
            "discovery_type": "emerging_market",
            "discovery_score": 0.43,
            "confidence": 0.85,
        }
    )

    print("[PASS] OEM-006 Discovery Engine Adapter")
    print(
        {
            "engine_id": engine.engine_id,
            "health": engine.health()["status"],
            "signals": len(result.signals),
            "predictions": len(predictions),
            "read_only": engine.read_only,
        }
    )
