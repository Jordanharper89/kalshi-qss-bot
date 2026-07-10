from qseries_v2.integration.oem_007_recall_ledger_engine_adapter import (
    ENGINE_ID,
    RecallLedgerEngineAdapter,
    build_engine,
)


def test_oem_007_adapter_health():
    engine = build_engine()
    health = engine.health()

    assert health["engine_id"] == ENGINE_ID
    assert health["status"] == "ok"
    assert health["details"]["read_only"] is True


def test_oem_007_adapter_analyze_produces_signals():
    engine = RecallLedgerEngineAdapter(engine=None)

    result = engine.analyze(
        {
            "market_id": "TEST-RECALL-YES",
            "ledger_key": "pattern_17",
            "recall_type": "historical_match",
            "recall_score": 0.39,
            "confidence": 0.82,
            "sample_size": 44,
        }
    )

    assert result.engine_id == ENGINE_ID
    assert result.status in {"ok", "degraded", "empty"}
    assert len(result.signals) == 1
    assert result.signals[0]["market_id"] == "TEST-RECALL-YES"
    assert result.signals[0]["ledger_key"] == "pattern_17"
    assert result.signals[0]["recall_type"] == "historical_match"
    assert result.signals[0]["confidence"] == 0.82


def test_oem_007_adapter_predicts_canonical_predictions():
    engine = RecallLedgerEngineAdapter(engine=None)

    predictions = engine.predict(
        {
            "market_id": "TEST-RECALL-YES",
            "ledger_key": "pattern_22",
            "recall_score": 0.46,
            "confidence": 0.87,
        }
    )

    assert len(predictions) == 1
    prediction = predictions[0]

    if isinstance(prediction, dict):
        assert prediction["engine_id"] == ENGINE_ID
        assert prediction["market_id"] == "TEST-RECALL-YES"
        assert prediction["side"] == "YES"
        assert prediction["confidence"] == 0.87
    else:
        assert prediction.engine_id == ENGINE_ID
        assert prediction.market_id == "TEST-RECALL-YES"
        assert prediction.side == "YES"
        assert prediction.confidence == 0.87


def test_oem_007_negative_recall_maps_to_no():
    engine = RecallLedgerEngineAdapter(engine=None)

    predictions = engine.predict(
        {
            "market_id": "TEST-RECALL-NO",
            "recall_score": -0.32,
            "confidence": 0.73,
        }
    )

    prediction = predictions[0]

    if isinstance(prediction, dict):
        assert prediction["side"] == "NO"
    else:
        assert prediction.side == "NO"


def test_oem_007_runtime_registration_shape():
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
    test_oem_007_adapter_health()
    test_oem_007_adapter_analyze_produces_signals()
    test_oem_007_adapter_predicts_canonical_predictions()
    test_oem_007_negative_recall_maps_to_no()
    test_oem_007_runtime_registration_shape()

    engine = build_engine()
    result = engine.analyze(
        {
            "market_id": "TEST-RECALL-YES",
            "ledger_key": "pattern_17",
            "recall_type": "historical_match",
            "recall_score": 0.39,
            "confidence": 0.82,
            "sample_size": 44,
        }
    )
    predictions = engine.predict(
        {
            "market_id": "TEST-RECALL-YES",
            "ledger_key": "pattern_22",
            "recall_score": 0.46,
            "confidence": 0.87,
        }
    )

    print("[PASS] OEM-007 Recall Ledger Engine Adapter")
    print(
        {
            "engine_id": engine.engine_id,
            "health": engine.health()["status"],
            "signals": len(result.signals),
            "predictions": len(predictions),
            "read_only": engine.read_only,
        }
    )
