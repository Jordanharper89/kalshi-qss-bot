from qseries_v2.oracle_intelligence.arbitrage_discovery_model.cross_venue_arbitrage_discovery_registry_bridge import (
    CrossVenueArbitrageDiscoveryRegistryBridge,
)


def test_adm_005_cross_venue_arbitrage_discovery_registry_bridge():
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

    bridge = CrossVenueArbitrageDiscoveryRegistryBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_and_bridge(
        raw_records,
        source_name="adm_005_test_source",
        min_net_edge_percent=0.001,
        min_liquidity=1000,
    )
    report_b = bridge.discover_and_bridge(
        list(reversed(raw_records)),
        source_name="adm_005_test_source",
        min_net_edge_percent=0.001,
        min_liquidity=1000,
    )

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["route_allowed"] is False
    assert caps["leg_execution_allowed"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "ADM-005"
    assert report_a.bridge_id == "oracle.discovery.bridge.cross_venue_arbitrage_registry"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.records) == 1

    keys_a = [r.registry_key for r in report_a.records]
    keys_b = [r.registry_key for r in report_b.records]
    assert keys_a == keys_b

    first = report_a.records[0]
    assert first.read_only is True
    assert first.registry_status == "registry_ready"
    assert first.symbol == "BTC-USD"
    assert first.buy_venue == "coinbase"
    assert first.sell_venue == "kraken"
    assert first.payload["read_only"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["order_allowed"] is False
    assert first.payload["route_allowed"] is False
    assert first.payload["leg_execution_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["execution_allowed"] is False
    assert first.payload["universal_market"]["market_type"] == "cross_venue_arbitrage"

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("registry payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "ADM-005"
    assert d["read_only"] is True
    assert d["telemetry"]["opportunities_seen"] == 1
    assert d["telemetry"]["records_emitted"] == 1
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["route_allowed"] is False

    print("[PASS] ADM-005 Cross-Venue Arbitrage Discovery Registry Bridge")
    print(
        {
            "schema_version": d["schema_version"],
            "bridge_id": d["bridge_id"],
            "status": d["status"],
            "records": len(d["records"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_adm_005_cross_venue_arbitrage_discovery_registry_bridge()
