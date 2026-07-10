from qseries_v2.oracle_intelligence.wallet_intelligence_discovery_model.wallet_intelligence_source_adapter import (
    WalletIntelligenceSourceAdapter,
)


def test_wdm_002_wallet_intelligence_source_adapter():
    raw_records = [
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
    ]

    adapter = WalletIntelligenceSourceAdapter(source_name="wdm_002_test_feed")
    caps = adapter.capabilities()
    health = adapter.health()

    batch_1 = adapter.normalize_batch(raw_records)
    batch_2 = adapter.normalize_batch(list(reversed(raw_records)))

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["signing_allowed"] is False
    assert caps["fund_movement_allowed"] is False
    assert caps["swap_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert batch_1.schema_version == "WDM-002"
    assert batch_1.adapter_id == "oracle.discovery.source.wallet_intelligence"
    assert batch_1.read_only is True
    assert len(batch_1.snapshots) == 2

    order_1 = [(s.wallet, s.symbol, s.tx_hash) for s in batch_1.snapshots]
    order_2 = [(s.wallet, s.symbol, s.tx_hash) for s in batch_2.snapshots]
    assert order_1 == order_2
    assert order_1 == [
        ("wallet_a", "WIF", "tx_a"),
        ("wallet_b", "BONK", "tx_b"),
    ]

    first = batch_1.snapshots[0]
    assert first.wallet == "wallet_a"
    assert first.chain == "solana"
    assert first.symbol == "WIF"
    assert first.token_address == "wif_mint"
    assert first.action == "accumulate"
    assert first.amount == 25000.0
    assert first.usd_value == 10000.0
    assert first.price == 0.40
    assert first.wallet_score == 0.93
    assert first.realized_pnl == 25000.0
    assert first.win_rate == 0.81
    assert first.holding_count == 8
    assert first.read_only is True
    assert first.metadata["source_name"] == "wdm_002_test_feed"

    try:
        first.metadata["new"] = "mutation"
        raise AssertionError("snapshot metadata should be immutable")
    except TypeError:
        pass

    d = batch_1.to_dict()
    assert d["schema_version"] == "WDM-002"
    assert d["read_only"] is True
    assert d["telemetry"]["raw_records_seen"] == 2
    assert d["telemetry"]["snapshots_emitted"] == 2
    assert d["telemetry"]["wallets_seen"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["signing_allowed"] is False

    print("[PASS] WDM-002 Wallet Intelligence Source Adapter")
    print(
        {
            "schema_version": d["schema_version"],
            "adapter_id": d["adapter_id"],
            "snapshots": len(d["snapshots"]),
            "wallets_seen": d["telemetry"]["wallets_seen"],
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_wdm_002_wallet_intelligence_source_adapter()
