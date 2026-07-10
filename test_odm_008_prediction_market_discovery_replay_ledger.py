from qseries_v2.oracle_intelligence.oracle_discovery_model.prediction_market_discovery_replay_ledger import (
    PredictionMarketDiscoveryReplayLedger,
)


def test_odm_008_prediction_market_discovery_replay_ledger():
    raw_markets = [
        {
            "ticker": "KX.ODM008.YES",
            "question": "Will ODM-008 fixture one resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 40,
            "model_probability": 54,
            "liquidity": 2500,
            "volume": 10000,
            "status": "open",
        },
        {
            "ticker": "KX.ODM008.NO",
            "question": "Will ODM-008 fixture two resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 76,
            "model_probability": 64,
            "liquidity": 3000,
            "volume": 15000,
            "status": "open",
        },
        {
            "ticker": "KX.ODM008.REJECT",
            "question": "Will ODM-008 low-edge fixture resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 50,
            "model_probability": 50.5,
            "liquidity": 3000,
            "status": "open",
        },
    ]

    ledger = PredictionMarketDiscoveryReplayLedger()
    caps = ledger.capabilities()
    health = ledger.health()

    baseline = ledger.run_discovery_and_record(
        raw_markets,
        source_name="odm_008_test_source",
        min_edge=0.02,
        min_liquidity=100,
    )
    replay = ledger.run_discovery_and_record(
        list(reversed(raw_markets)),
        source_name="odm_008_test_source",
        min_edge=0.02,
        min_liquidity=100,
    )

    comparison = ledger.compare(baseline, replay)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["deterministic"] is True
    assert caps["canonicalizes_volatile_fields"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert baseline.schema_version == "ODM-008.1"
    assert baseline.ledger_id == "oracle.discovery.ledger.prediction_market_replay"
    assert baseline.status == "passed"
    assert baseline.read_only is True
    assert len(baseline.entries) == 2

    assert baseline.run_fingerprint == replay.run_fingerprint
    assert comparison.matching is True
    assert comparison.status == "matched"
    assert comparison.read_only is True

    first = baseline.entries[0]
    assert first.read_only is True
    assert first.replay_status == "recorded"
    assert first.packet_fingerprint
    assert first.payload_fingerprint
    assert first.audit_fingerprint
    assert first.payload_summary["validation_required"] is True
    assert first.payload_summary["ranking_required"] is True
    assert first.payload_summary["registry_required"] is True
    assert first.payload_summary["execution_allowed"] is False
    assert first.payload_summary["read_only"] is True

    try:
        first.payload_summary["execution_allowed"] = True
        raise AssertionError("payload summary should be immutable")
    except TypeError:
        pass

    d = baseline.to_dict()
    c = comparison.to_dict()

    assert d["schema_version"] == "ODM-008.1"
    assert d["read_only"] is True
    assert d["telemetry"]["packets_seen"] == 2
    assert d["telemetry"]["entries_emitted"] == 2
    assert "created_at" in d["telemetry"]["volatile_fields_excluded"]
    assert c["matching"] is True
    assert c["baseline_entries"] == 2
    assert c["replay_entries"] == 2

    print("[PASS] ODM-008.1 Prediction Market Discovery Replay Ledger Determinism Fix")
    print(
        {
            "schema_version": d["schema_version"],
            "ledger_id": d["ledger_id"],
            "status": d["status"],
            "entries": len(d["entries"]),
            "replay_match": c["matching"],
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_odm_008_prediction_market_discovery_replay_ledger()
