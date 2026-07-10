from qseries_v2.integration.oem_008_query_audit_engine_adapter import (
    ENGINE_ID,
    QueryAuditEngineAdapter,
    build_engine,
)


def test_oem_008_adapter_health():
    engine = build_engine()
    health = engine.health()

    assert health["engine_id"] == ENGINE_ID
    assert health["status"] == "ok"
    assert health["details"]["read_only"] is True


def test_oem_008_adapter_analyze_produces_signals():
    engine = QueryAuditEngineAdapter(engine=None)

    result = engine.analyze(
        {
            "market_id": "TEST-AUDIT-YES",
            "query_id": "query_185",
            "audit_type": "resolver_quality",
            "audit_status": "passed",
            "audit_score": 0.41,
            "confidence": 0.83,
        }
    )

    assert result.engine_id == ENGINE_ID
    assert result.status in {"ok", "degraded", "empty"}
    assert len(result.signals) == 1
    assert result.signals[0]["market_id"] == "TEST-AUDIT-YES"
    assert result.signals[0]["query_id"] == "query_185"
    assert result.signals[0]["audit_type"] == "resolver_quality"
    assert result.signals[0]["confidence"] == 0.83


def test_oem_008_adapter_predicts_canonical_predictions():
    engine = QueryAuditEngineAdapter(engine=None)

    predictions = engine.predict(
        {
            "market_id": "TEST-AUDIT-YES",
            "query_id": "query_186",
            "audit_score": 0.48,
            "confidence": 0.88,
        }
    )

    assert len(predictions) == 1
    prediction = predictions[0]

    if isinstance(prediction, dict):
        assert prediction["engine_id"] == ENGINE_ID
        assert prediction["market_id"] == "TEST-AUDIT-YES"
        assert prediction["side"] == "YES"
        assert prediction["confidence"] == 0.88
    else:
        assert prediction.engine_id == ENGINE_ID
        assert prediction.market_id == "TEST-AUDIT-YES"
        assert prediction.side == "YES"
        assert prediction.confidence == 0.88


def test_oem_008_negative_audit_maps_to_no():
    engine = QueryAuditEngineAdapter(engine=None)

    predictions = engine.predict(
        {
            "market_id": "TEST-AUDIT-NO",
            "audit_score": -0.35,
            "confidence": 0.75,
        }
    )

    prediction = predictions[0]

    if isinstance(prediction, dict):
        assert prediction["side"] == "NO"
    else:
        assert prediction.side == "NO"


def test_oem_008_runtime_registration_shape():
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
    test_oem_008_adapter_health()
    test_oem_008_adapter_analyze_produces_signals()
    test_oem_008_adapter_predicts_canonical_predictions()
    test_oem_008_negative_audit_maps_to_no()
    test_oem_008_runtime_registration_shape()

    engine = build_engine()
    result = engine.analyze(
        {
            "market_id": "TEST-AUDIT-YES",
            "query_id": "query_185",
            "audit_type": "resolver_quality",
            "audit_status": "passed",
            "audit_score": 0.41,
            "confidence": 0.83,
        }
    )
    predictions = engine.predict(
        {
            "market_id": "TEST-AUDIT-YES",
            "query_id": "query_186",
            "audit_score": 0.48,
            "confidence": 0.88,
        }
    )

    print("[PASS] OEM-008 Query Audit Engine Adapter")
    print(
        {
            "engine_id": engine.engine_id,
            "health": engine.health()["status"],
            "signals": len(result.signals),
            "predictions": len(predictions),
            "read_only": engine.read_only,
        }
    )
