from qseries_v2.oracle_intelligence.universal_market_adapter_replay_search_engine import create_replay_search_engine

def test_oi_192_replay_search_engine():
    engine = create_replay_search_engine("oracle.test")
    records = [
        {"registration_id": "reg-001", "certification_id": "cert-001", "manifest_id": "manifest-001", "adapter_id": "adp.kalshi", "market_type": "prediction_market", "symbol": "TESTA", "status": "registered", "certification_level": "certified", "certified": True, "confidence": 0.91},
        {"registration_id": "reg-002", "certification_id": "cert-002", "manifest_id": "manifest-002", "adapter_id": "adp.kalshi", "market_type": "prediction_market", "symbol": "TESTB", "status": "registered", "certification_level": "certified_with_warnings", "certified": True, "confidence": 0.74},
        {"registration_id": "reg-003", "certification_id": "cert-003", "manifest_id": "manifest-003", "adapter_id": "adp.polymarket", "market_type": "prediction_market", "symbol": "TESTC", "status": "rejected", "certification_level": "not_certified", "certified": False, "confidence": 0.42},
    ]
    load = engine.load_registry_records(records)
    assert load.passed is True
    result = engine.search_by_adapter("adp.kalshi")
    assert result.passed is True
    assert result.record_count == 2
    assert len(result.records) == 2
    assert result.read_only_guardrails["execution_owner"] == "Q_SERIES_ONLY"
    assert engine.latest_result() is not None

if __name__ == "__main__":
    test_oi_192_replay_search_engine()
    print("[PASS] OI-192 Universal Market Adapter Replay Search Engine")
