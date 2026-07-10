from qseries_v2.oracle_intelligence.crypto_discovery_model.crypto_spot_discovery_registry_bridge import (
    CryptoSpotDiscoveryRegistryBridge,
)


def test_cdm_005_crypto_spot_discovery_registry_bridge():
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

    bridge = CryptoSpotDiscoveryRegistryBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_and_bridge(
        raw_records,
        source_name="cdm_005_test_source",
        min_edge_percent=0.01,
        min_liquidity=1000,
    )
    report_b = bridge.discover_and_bridge(
        list(reversed(raw_records)),
        source_name="cdm_005_test_source",
        min_edge_percent=0.01,
        min_liquidity=1000,
    )

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "CDM-005"
    assert report_a.bridge_id == "oracle.discovery.bridge.crypto_spot_registry"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.records) == 2

    keys_a = [r.registry_key for r in report_a.records]
    keys_b = [r.registry_key for r in report_b.records]
    assert keys_a == keys_b

    first = report_a.records[0]
    assert first.read_only is True
    assert first.registry_status == "registry_ready"
    assert first.payload["read_only"] is True
    assert first.payload["execution_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["execution_allowed"] is False
    assert first.payload["universal_market"]["market_type"] == "crypto_spot"

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("registry payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "CDM-005"
    assert d["read_only"] is True
    assert d["telemetry"]["opportunities_seen"] == 2
    assert d["telemetry"]["records_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] CDM-005 Crypto Spot Discovery Registry Bridge")
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
    test_cdm_005_crypto_spot_discovery_registry_bridge()
