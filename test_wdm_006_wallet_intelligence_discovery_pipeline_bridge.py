from qseries_v2.oracle_intelligence.wallet_intelligence_discovery_model.wallet_intelligence_discovery_pipeline_bridge import (
    WalletIntelligenceDiscoveryPipelineBridge,
)


def test_wdm_006_wallet_intelligence_discovery_pipeline_bridge():
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

    bridge = WalletIntelligenceDiscoveryPipelineBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_registry_and_bridge(
        raw_records,
        source_name="wdm_006_test_source",
        min_wallet_score=0.70,
        min_usd_value=1000,
        min_signal_score=0.55,
    )
    report_b = bridge.discover_registry_and_bridge(
        list(reversed(raw_records)),
        source_name="wdm_006_test_source",
        min_wallet_score=0.70,
        min_usd_value=1000,
        min_signal_score=0.55,
    )

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["signing_allowed"] is False
    assert caps["fund_movement_allowed"] is False
    assert caps["swap_allowed"] is False
    assert caps["deterministic"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "WDM-006"
    assert report_a.bridge_id == "oracle.discovery.bridge.wallet_intelligence_pipeline"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.packets) == 2

    packet_ids_a = [p.packet_id for p in report_a.packets]
    packet_ids_b = [p.packet_id for p in report_b.packets]
    assert packet_ids_a == packet_ids_b

    first = report_a.packets[0]
    assert first.read_only is True
    assert first.pipeline_status == "pipeline_ready"
    assert first.payload["read_only"] is True
    assert first.payload["validation_required"] is True
    assert first.payload["ranking_required"] is True
    assert first.payload["registry_required"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["signing_allowed"] is False
    assert first.payload["fund_movement_allowed"] is False
    assert first.payload["swap_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["handoff_target"] == "OOS Opportunity Pipeline"

    assert first.payload["registry_payload"]["universal_market"]["market_type"] == "wallet_intelligence"
    assert first.payload["registry_payload"]["read_only"] is True
    assert first.payload["registry_payload"]["execution_allowed"] is False
    assert first.payload["registry_payload"]["signing_allowed"] is False
    assert first.payload["registry_payload"]["fund_movement_allowed"] is False

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("pipeline payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "WDM-006"
    assert d["read_only"] is True
    assert d["telemetry"]["records_seen"] == 2
    assert d["telemetry"]["packets_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["signing_allowed"] is False
    assert d["telemetry"]["fund_movement_allowed"] is False

    print("[PASS] WDM-006 Wallet Intelligence Discovery Pipeline Bridge")
    print(
        {
            "schema_version": d["schema_version"],
            "bridge_id": d["bridge_id"],
            "status": d["status"],
            "packets": len(d["packets"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_wdm_006_wallet_intelligence_discovery_pipeline_bridge()
