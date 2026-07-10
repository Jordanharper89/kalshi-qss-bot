from qseries_v2.oracle_intelligence.wallet_intelligence_discovery_model.wallet_intelligence_discovery_replay_ledger import (
    WalletIntelligenceDiscoveryReplayLedger,
)


def test_wdm_008_wallet_intelligence_discovery_replay_ledger():
    raw_records = [
        {
            "address": "wallet_a",
            "network": "solana",
            "token_symbol": "WIF",
            "token_address": "wif_mint",
            "type": "accumulate",
            "token_amount": 25000,
            "value_usd": 10000,
            "token_price": 0.40,
            "tx_hash": "tx_a",
            "block_time": "2026-01-01T00:01:00Z",
            "wallet_score": 0.93,
            "realized_pnl": 25000,
            "win_rate": 0.81,
            "holding_count": 8,
        },
        {
            "wallet": "wallet_b",
            "chain": "Solana",
            "symbol": "BONK",
            "mint": "bonk_mint",
            "action": "buy",
            "amount": 1000000,
            "usd_value": 5000,
            "price": 0.005,
            "signature": "tx_b",
            "timestamp": "2026-01-01T00:02:00Z",
            "smart_money_score": 0.88,
            "pnl": 12000,
            "win_rate": 0.72,
            "positions": 15,
        },
        {
            "wallet": "wallet_c",
            "chain": "solana",
            "symbol": "LOW",
            "mint": "low_mint",
            "action": "buy",
            "amount": 100,
            "usd_value": 100,
            "price": 1.0,
            "signature": "tx_c",
            "timestamp": "2026-01-01T00:03:00Z",
            "smart_money_score": 0.20,
            "pnl": 0,
            "win_rate": 0.20,
            "positions": 1,
        },
    ]

    ledger = WalletIntelligenceDiscoveryReplayLedger()
    caps = ledger.capabilities()
    health = ledger.health()

    baseline = ledger.run_discovery_and_record(
        raw_records,
        source_name="wdm_008_test_source",
        min_wallet_score=0.70,
        min_usd_value=1000,
        min_signal_score=0.55,
    )
    replay = ledger.run_discovery_and_record(
        list(reversed(raw_records)),
        source_name="wdm_008_test_source",
        min_wallet_score=0.70,
        min_usd_value=1000,
        min_signal_score=0.55,
    )
    comparison = ledger.compare(baseline, replay)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["signing_allowed"] is False
    assert caps["fund_movement_allowed"] is False
    assert caps["swap_allowed"] is False
    assert caps["deterministic"] is True
    assert caps["canonicalizes_volatile_fields"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert baseline.schema_version == "WDM-008"
    assert baseline.ledger_id == "oracle.discovery.ledger.wallet_intelligence_replay"
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
    assert first.payload_summary["signing_allowed"] is False
    assert first.payload_summary["fund_movement_allowed"] is False
    assert first.payload_summary["swap_allowed"] is False
    assert first.payload_summary["read_only"] is True

    try:
        first.payload_summary["execution_allowed"] = True
        raise AssertionError("payload summary should be immutable")
    except TypeError:
        pass

    d = baseline.to_dict()
    c = comparison.to_dict()

    assert d["schema_version"] == "WDM-008"
    assert d["read_only"] is True
    assert d["telemetry"]["packets_seen"] == 2
    assert d["telemetry"]["entries_emitted"] == 2
    assert "created_at" in d["telemetry"]["volatile_fields_excluded"]
    assert c["matching"] is True
    assert c["baseline_entries"] == 2
    assert c["replay_entries"] == 2

    print("[PASS] WDM-008 Wallet Intelligence Discovery Replay Ledger")
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
    test_wdm_008_wallet_intelligence_discovery_replay_ledger()
