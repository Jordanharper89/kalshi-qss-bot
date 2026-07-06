from qseries_v2.oracle_intelligence.universal_market_adapter_replay_filter_engine import ReplayFilterCriteria, create_replay_filter_engine

def test_oi_193_replay_filter_engine():
    engine = create_replay_filter_engine("oracle.test")
    records = [
        {"registration_id": "reg-001", "certification_id": "cert-001", "manifest_id": "manifest-001", "adapter_id": "adp.kalshi", "market_type": "prediction_market", "symbol": "TESTA", "status": "registered", "certification_level": "certified", "certified": True, "confidence": 0.91},
        {"registration_id": "reg-002", "certification_id": "cert-002", "manifest_id": "manifest-002", "adapter_id": "adp.kalshi", "market_type": "prediction_market", "symbol": "TESTB", "status": "registered", "certification_level": "certified_with_warnings", "certified": True, "confidence": 0.74},
        {"registration_id": "reg-003", "certification_id": "cert-003", "manifest_id": "manifest-003", "adapter_id": "adp.polymarket", "market_type": "prediction_market", "symbol": "TESTC", "status": "rejected", "certification_level": "not_certified", "certified": False, "confidence": 0.42},
    ]
    result = engine.filter_records(records, {"certified": True, "min_confidence": 0.70})
    assert result.passed is True
    assert result.record_count == 2
    assert len(result.records) == 2
    assert result.metadata["rejected_count"] == 1
    assert ReplayFilterCriteria({"certified": True}).criteria["certified"] is True
    assert result.read_only_guardrails["oracle_read_only"] is True

if __name__ == "__main__":
    test_oi_193_replay_filter_engine()
    print("[PASS] OI-193 Universal Market Adapter Replay Filter Engine")
