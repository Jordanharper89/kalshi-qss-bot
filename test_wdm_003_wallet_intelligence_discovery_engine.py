from qseries_v2.oracle_intelligence.wallet_intelligence_discovery_model.wallet_intelligence_discovery_contract import (
    WalletIntelligenceDiscoveryRequest,
    WalletIntelligenceFamily,
)
from qseries_v2.oracle_intelligence.wallet_intelligence_discovery_model.wallet_intelligence_discovery_engine import (
    WalletIntelligenceDiscoveryEngine,
)


def test_wdm_003_wallet_intelligence_discovery_engine():
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

    request = WalletIntelligenceDiscoveryRequest(
        request_id="wdm003.test.request",
        family=WalletIntelligenceFamily.SMART_MONEY,
        source_name="wdm_003_test_feed",
        chains=("solana",),
        wallets=("wallet_a", "wallet_b", "wallet_c"),
        symbols=("WIF", "BONK", "LOW"),
        metadata={"raw_records": raw_records},
    )

    engine = WalletIntelligenceDiscoveryEngine(
        min_wallet_score=0.70,
        min_usd_value=1000,
        min_signal_score=0.55,
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
    assert health.status == "ok"
    assert health.read_only is True

    assert report_1.schema_version == "WDM-001"
    assert report_1.engine_id == "oracle.discovery.wallet_intelligence"
    assert report_1.status == "passed"
    assert report_1.read_only is True
    assert len(report_1.opportunities) == 2

    ids_1 = [o.opportunity_id for o in report_1.opportunities]
    ids_2 = [o.opportunity_id for o in report_2.opportunities]
    assert ids_1 == ids_2

    first = report_1.opportunities[0]
    assert first.read_only is True
    assert first.opportunity_type == "wallet_intelligence_signal"
    assert first.source_engine_id == "oracle.discovery.wallet_intelligence"
    assert first.signal_type in {"smart_money_accumulation", "smart_money_distribution", "wallet_activity_observation"}
    assert first.signal_score >= 0.55
    assert 0.0 <= first.confidence <= 1.0
    assert first.usd_value >= 1000
    assert first.wallet_score >= 0.70
    assert first.status == "discovered"
    assert first.universal_market["market_type"] == "wallet_intelligence"
    assert first.universal_market["read_only"] is True
    assert first.universal_market["execution_allowed"] is False
    assert first.universal_market["signing_allowed"] is False
    assert first.universal_market["fund_movement_allowed"] is False
    assert first.explanation["rules"]

    try:
        first.universal_market["execution_allowed"] = True
        raise AssertionError("universal_market should be immutable")
    except TypeError:
        pass

    d = report_1.to_dict()
    assert d["read_only"] is True
    assert d["telemetry"]["records_seen"] == 3
    assert d["telemetry"]["wallets_seen"] == 3
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["rejected_records"] == 1
    assert d["telemetry"]["read_only"] is True

    print("[PASS] WDM-003 Wallet Intelligence Discovery Engine")
    print(
        {
            "schema_version": "WDM-003",
            "engine_id": d["engine_id"],
            "status": d["status"],
            "opportunities": len(d["opportunities"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_wdm_003_wallet_intelligence_discovery_engine()
