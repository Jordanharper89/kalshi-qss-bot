from qseries_v2.oracle_intelligence.solana_launch_discovery_model.solana_launch_source_adapter import (
    SolanaLaunchSourceAdapter,
)


def test_sld_002_solana_launch_source_adapter():
    raw_records = [
        {
            "mint": "mint_b",
            "symbol": "BETA",
            "name": "Beta Token",
            "pool": "pool_b",
            "dex": "Raydium",
            "quote": "SOL",
            "liquidity": 25000,
            "market_cap": 120000,
            "volume_5m": 8000,
            "holders": 120,
            "age": 90,
            "mint_disabled": True,
            "freeze_disabled": True,
            "liquidity_burned": True,
            "status": "active",
            "creator": "wallet_b",
            "signature": "tx_b",
            "timestamp": "2026-01-01T00:02:00Z",
        },
        {
            "token_mint": "mint_a",
            "ticker": "ALPHA",
            "name": "Alpha Token",
            "pool_address": "pool_a",
            "dex": "raydium",
            "quote_asset": "SOL",
            "liquidity_usd": 50000,
            "market_cap_usd": 200000,
            "volume_5m_usd": 15000,
            "holder_count": 250,
            "age_seconds": 30,
            "mint_authority_disabled": True,
            "freeze_authority_disabled": True,
            "lp_burned": True,
            "pool_status": "active",
            "deployer_wallet": "wallet_a",
            "tx_signature": "tx_a",
            "detected_at": "2026-01-01T00:01:00Z",
        },
    ]

    adapter = SolanaLaunchSourceAdapter(source_name="sld_002_test_feed")
    caps = adapter.capabilities()
    health = adapter.health()

    batch_1 = adapter.normalize_batch(raw_records)
    batch_2 = adapter.normalize_batch(list(reversed(raw_records)))

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["signing_allowed"] is False
    assert caps["fund_movement_allowed"] is False
    assert caps["swap_allowed"] is False
    assert caps["snipe_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert batch_1.schema_version == "SLD-002"
    assert batch_1.adapter_id == "oracle.discovery.source.solana_launch"
    assert batch_1.read_only is True
    assert len(batch_1.snapshots) == 2

    order_1 = [(s.symbol, s.mint, s.pool_address) for s in batch_1.snapshots]
    order_2 = [(s.symbol, s.mint, s.pool_address) for s in batch_2.snapshots]
    assert order_1 == order_2
    assert order_1 == [
        ("ALPHA", "mint_a", "pool_a"),
        ("BETA", "mint_b", "pool_b"),
    ]

    first = batch_1.snapshots[0]
    assert first.symbol == "ALPHA"
    assert first.mint == "mint_a"
    assert first.pool_address == "pool_a"
    assert first.dex == "raydium"
    assert first.quote_asset == "SOL"
    assert first.liquidity_usd == 50000.0
    assert first.market_cap_usd == 200000.0
    assert first.volume_5m_usd == 15000.0
    assert first.holder_count == 250
    assert first.age_seconds == 30.0
    assert first.mint_authority_disabled is True
    assert first.freeze_authority_disabled is True
    assert first.lp_burned is True
    assert first.read_only is True
    assert first.metadata["source_name"] == "sld_002_test_feed"

    try:
        first.metadata["new"] = "mutation"
        raise AssertionError("snapshot metadata should be immutable")
    except TypeError:
        pass

    d = batch_1.to_dict()
    assert d["schema_version"] == "SLD-002"
    assert d["read_only"] is True
    assert d["telemetry"]["raw_records_seen"] == 2
    assert d["telemetry"]["snapshots_emitted"] == 2
    assert d["telemetry"]["launches_seen"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["signing_allowed"] is False

    print("[PASS] SLD-002 Solana Launch Source Adapter")
    print(
        {
            "schema_version": d["schema_version"],
            "adapter_id": d["adapter_id"],
            "snapshots": len(d["snapshots"]),
            "launches_seen": d["telemetry"]["launches_seen"],
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_sld_002_solana_launch_source_adapter()
