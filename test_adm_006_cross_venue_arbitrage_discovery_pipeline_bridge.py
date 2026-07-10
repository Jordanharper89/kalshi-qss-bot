from qseries_v2.oracle_intelligence.arbitrage_discovery_model.cross_venue_arbitrage_discovery_pipeline_bridge import (
    CrossVenueArbitrageDiscoveryPipelineBridge,
)


def test_adm_006_cross_venue_arbitrage_discovery_pipeline_bridge():
    raw_records = [
        {
            "symbol": "BTC-USD",
            "venue": "coinbase",
            "bid": 65000,
            "ask": 65020,
            "last_price": 65010,
            "fee_bps": 8,
            "liquidity": 2500000,
            "volume_24h": 5000000,
            "latency_ms": 40,
            "status": "active",
        },
        {
            "symbol": "BTC/USD",
            "exchange": "kraken",
            "bid": 65300,
            "ask": 65320,
            "last": 65310,
            "taker_fee_bps": 10,
            "depth": 1500000,
            "volume": 4000000,
            "latency_ms": 80,
            "status": "active",
        },
        {
            "pair": "ETH/USD",
            "venue": "coinbase",
            "best_bid": 3500,
            "best_ask": 3502,
            "price": 3501,
            "fee_bps": 8,
            "liquidity": 800000,
            "volume_24h": 2000000,
            "status": "active",
        },
    ]

    bridge = CrossVenueArbitrageDiscoveryPipelineBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_registry_and_bridge(
        raw_records,
        source_name="adm_006_test_source",
        min_net_edge_percent=0.001,
        min_liquidity=1000,
    )
    report_b = bridge.discover_registry_and_bridge(
        list(reversed(raw_records)),
        source_name="adm_006_test_source",
        min_net_edge_percent=0.001,
        min_liquidity=1000,
    )

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["route_allowed"] is False
    assert caps["leg_execution_allowed"] is False
    assert caps["deterministic"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "ADM-006"
    assert report_a.bridge_id == "oracle.discovery.bridge.cross_venue_arbitrage_pipeline"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.packets) == 1

    packet_ids_a = [p.packet_id for p in report_a.packets]
    packet_ids_b = [p.packet_id for p in report_b.packets]
    assert packet_ids_a == packet_ids_b

    first = report_a.packets[0]
    assert first.read_only is True
    assert first.pipeline_status == "pipeline_ready"
    assert first.symbol == "BTC-USD"
    assert first.buy_venue == "coinbase"
    assert first.sell_venue == "kraken"
    assert first.payload["read_only"] is True
    assert first.payload["validation_required"] is True
    assert first.payload["ranking_required"] is True
    assert first.payload["registry_required"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["order_allowed"] is False
    assert first.payload["route_allowed"] is False
    assert first.payload["leg_execution_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["handoff_target"] == "OOS Opportunity Pipeline"

    assert first.payload["registry_payload"]["universal_market"]["market_type"] == "cross_venue_arbitrage"
    assert first.payload["registry_payload"]["read_only"] is True
    assert first.payload["registry_payload"]["execution_allowed"] is False

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("pipeline payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "ADM-006"
    assert d["read_only"] is True
    assert d["telemetry"]["records_seen"] == 1
    assert d["telemetry"]["packets_emitted"] == 1
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["route_allowed"] is False

    print("[PASS] ADM-006 Cross-Venue Arbitrage Discovery Pipeline Bridge")
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
    test_adm_006_cross_venue_arbitrage_discovery_pipeline_bridge()
