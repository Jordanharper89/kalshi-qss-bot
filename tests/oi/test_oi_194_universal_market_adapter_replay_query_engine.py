from qseries_v2.oracle_intelligence.universal_market_adapter_replay_query_engine import create_replay_query_engine

def test_oi_194_replay_query_engine():
    engine = create_replay_query_engine("oracle.test")
    records = [
        {"registration_id": "reg-001", "certification_id": "cert-001", "manifest_id": "manifest-001", "adapter_id": "adp.kalshi", "market_type": "prediction_market", "symbol": "TESTA", "status": "registered", "certification_level": "certified", "certified": True, "confidence": 0.91},
        {"registration_id": "reg-002", "certification_id": "cert-002", "manifest_id": "manifest-002", "adapter_id": "adp.kalshi", "market_type": "prediction_market", "symbol": "TESTB", "status": "registered", "certification_level": "certified_with_warnings", "certified": True, "confidence": 0.74},
        {"registration_id": "reg-003", "certification_id": "cert-003", "manifest_id": "manifest-003", "adapter_id": "adp.polymarket", "market_type": "prediction_market", "symbol": "TESTC", "status": "rejected", "certification_level": "not_certified", "certified": False, "confidence": 0.42},
    ]
    result = engine.query(records, {"select": ["registration_id", "confidence"], "sort_by": "confidence", "sort_order": "desc", "limit": 2})
    assert result.passed is True
    assert result.record_count == 2
    assert result.records[0]["confidence"] >= result.records[1]["confidence"]
    assert set(result.records[0].keys()) == {"registration_id", "confidence"}
    assert result.read_only_guardrails["execution_owner"] == "Q_SERIES_ONLY"

if __name__ == "__main__":
    test_oi_194_replay_query_engine()
    print("[PASS] OI-194 Universal Market Adapter Replay Query Engine")
