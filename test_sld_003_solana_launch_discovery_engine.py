from qseries_v2.oracle_intelligence.solana_launch_discovery_model.solana_launch_discovery_contract import (
    SolanaLaunchDiscoveryFamily,
    SolanaLaunchDiscoveryRequest,
)
from qseries_v2.oracle_intelligence.solana_launch_discovery_model.solana_launch_discovery_engine import (
    SolanaLaunchDiscoveryEngine,
)


def test_sld_003_solana_launch_discovery_engine():
    raw_records = [
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
            "mint": "mint_bad",
            "symbol": "BAD",
            "pool": "pool_bad",
            "liquidity": 100,
            "age": 900,
            "mint_disabled": False,
            "freeze_disabled": False,
            "liquidity_burned": False,
            "status": "active",
        },
    ]

    request = SolanaLaunchDiscoveryRequest(
        request_id="sld003.test.request",
        family=SolanaLaunchDiscoveryFamily.NEW_TOKEN_LAUNCH,
        source_name="sld_003_test_feed",
        mints=("mint_a", "mint_b", "mint_bad"),
        pools=("pool_a", "pool_b", "pool_bad"),
        metadata={"raw_records": raw_records},
    )

    engine = SolanaLaunchDiscoveryEngine(
        min_liquidity_usd=1000,
        max_age_seconds=600,
        min_launch_score=0.55,
    )

    caps = engine.capabilities()
    health = engine.health()
    report_1 = engine.discover(request)
    report_2 = engine.discover(request)

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.telemetry is True
    assert caps.metadata["signing_allowed"] is False
    assert caps.metadata["fund_movement_allowed"] is False
    assert caps.metadata["swap_allowed"] is False
    assert caps.metadata["snipe_allowed"] is False
    assert health.status == "ok"
    assert health.read_only is True

    assert report_1.schema_version == "SLD-001"
    assert report_1.engine_id == "oracle.discovery.solana_launch"
    assert report_1.status == "passed"
    assert report_1.read_only is True
    assert len(report_1.opportunities) == 2

    ids_1 = [o.opportunity_id for o in report_1.opportunities]
    ids_2 = [o.opportunity_id for o in report_2.opportunities]
    assert ids_1 == ids_2

    first = report_1.opportunities[0]
    assert first.read_only is True
    assert first.opportunity_type == "solana_launch_signal"
    assert first.source_engine_id == "oracle.discovery.solana_launch"
    assert first.launch_score >= 0.55
    assert 0.0 <= first.confidence <= 1.0
    assert first.liquidity_usd >= 1000
    assert first.age_seconds <= 600
    assert first.status == "discovered"
    assert first.universal_market["market_type"] == "solana_launch"
    assert first.universal_market["read_only"] is True
    assert first.universal_market["execution_allowed"] is False
    assert first.universal_market["signing_allowed"] is False
    assert first.universal_market["fund_movement_allowed"] is False
    assert first.universal_market["swap_allowed"] is False
    assert first.universal_market["snipe_allowed"] is False
    assert first.explanation["rules"]

    try:
        first.universal_market["execution_allowed"] = True
        raise AssertionError("universal_market should be immutable")
    except TypeError:
        pass

    d = report_1.to_dict()
    assert d["read_only"] is True
    assert d["telemetry"]["records_seen"] == 3
    assert d["telemetry"]["launches_seen"] == 3
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["rejected_records"] == 1
    assert d["telemetry"]["read_only"] is True

    print("[PASS] SLD-003 Solana Launch Discovery Engine")
    print(
        {
            "schema_version": "SLD-003",
            "engine_id": d["engine_id"],
            "status": d["status"],
            "opportunities": len(d["opportunities"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_sld_003_solana_launch_discovery_engine()
