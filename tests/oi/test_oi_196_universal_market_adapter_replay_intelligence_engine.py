from qseries_v2.oracle_intelligence.universal_market_adapter_replay_analytics_engine import create_replay_analytics_engine
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_intelligence_engine import create_replay_intelligence_engine

def test_oi_196_replay_intelligence_engine():
    records = [
        {"registration_id": "reg-001", "certification_id": "cert-001", "manifest_id": "manifest-001", "adapter_id": "adp.kalshi", "market_type": "prediction_market", "symbol": "TESTA", "status": "registered", "certification_level": "certified", "certified": True, "confidence": 0.91},
        {"registration_id": "reg-002", "certification_id": "cert-002", "manifest_id": "manifest-002", "adapter_id": "adp.kalshi", "market_type": "prediction_market", "symbol": "TESTB", "status": "registered", "certification_level": "certified_with_warnings", "certified": True, "confidence": 0.74},
        {"registration_id": "reg-003", "certification_id": "cert-003", "manifest_id": "manifest-003", "adapter_id": "adp.polymarket", "market_type": "prediction_market", "symbol": "TESTC", "status": "rejected", "certification_level": "not_certified", "certified": False, "confidence": 0.42},
    ]
    analytics = create_replay_analytics_engine("oracle.test").analyze(records)
    engine = create_replay_intelligence_engine("oracle.test")
    result = engine.generate_intelligence(records, analytics=analytics, context={"test": True})
    assert result.passed is True
    assert result.record_count == 1
    assert result.metadata["record_count"] == 3
    assert result.metadata["certified_count"] == 2
    assert result.metadata["quality_score"] > 0
    assert engine.latest_report() is not None
    assert result.read_only_guardrails["execution_owner"] == "Q_SERIES_ONLY"

if __name__ == "__main__":
    test_oi_196_replay_intelligence_engine()
    print("[PASS] OI-196 Universal Market Adapter Replay Intelligence Engine")
