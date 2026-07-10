from qseries_v2.oracle_intelligence.crypto_discovery_model.crypto_spot_discovery_replay_ledger import (
    CryptoSpotDiscoveryReplayLedger,
)


def test_cdm_008_crypto_spot_discovery_replay_ledger():
    raw_records = [
        {
            "symbol": "BTC-USD",
            "exchange": "coinbase",
            "price": 65000,
            "fair_value": 67000,
            "bid": 64990,
            "ask": 65010,
            "volume": 5000000,
            "depth": 2500000,
            "volatility_24h": 0.03,
            "status": "active",
        },
        {
            "symbol": "ETH/USD",
            "exchange": "coinbase",
            "price": 3500,
            "model_price": 3400,
            "bid": 3499,
            "ask": 3501,
            "volume_24h": 1000000,
            "liquidity": 500000,
            "volatility": 0.04,
            "status": "active",
        },
        {
            "symbol": "SOL-USD",
            "exchange": "coinbase",
            "price": 150,
            "fair_value": 151,
            "volume": 1000000,
            "depth": 500000,
            "status": "active",
        },
    ]

    ledger = CryptoSpotDiscoveryReplayLedger()
    caps = ledger.capabilities()
    health = ledger.health()

    baseline = ledger.run_discovery_and_record(
        raw_records,
        source_name="cdm_008_test_source",
        min_edge_percent=0.01,
        min_liquidity=1000,
    )
    replay = ledger.run_discovery_and_record(
        list(reversed(raw_records)),
        source_name="cdm_008_test_source",
        min_edge_percent=0.01,
        min_liquidity=1000,
    )
    comparison = ledger.compare(baseline, replay)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["swap_allowed"] is False
    assert caps["order_allowed"] is False
    assert caps["deterministic"] is True
    assert caps["canonicalizes_volatile_fields"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert baseline.schema_version == "CDM-008"
    assert baseline.ledger_id == "oracle.discovery.ledger.crypto_spot_replay"
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
    assert first.payload_summary["swap_allowed"] is False
    assert first.payload_summary["order_allowed"] is False
    assert first.payload_summary["read_only"] is True

    try:
        first.payload_summary["execution_allowed"] = True
        raise AssertionError("payload summary should be immutable")
    except TypeError:
        pass

    d = baseline.to_dict()
    c = comparison.to_dict()

    assert d["schema_version"] == "CDM-008"
    assert d["read_only"] is True
    assert d["telemetry"]["packets_seen"] == 2
    assert d["telemetry"]["entries_emitted"] == 2
    assert "created_at" in d["telemetry"]["volatile_fields_excluded"]
    assert c["matching"] is True
    assert c["baseline_entries"] == 2
    assert c["replay_entries"] == 2

    print("[PASS] CDM-008 Crypto Spot Discovery Replay Ledger")
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
    test_cdm_008_crypto_spot_discovery_replay_ledger()
