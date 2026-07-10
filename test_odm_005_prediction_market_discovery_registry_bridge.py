from qseries_v2.oracle_intelligence.oracle_discovery_model.prediction_market_discovery_registry_bridge import (
    PredictionMarketDiscoveryRegistryBridge,
)


def test_odm_005_prediction_market_discovery_registry_bridge():
    raw_markets = [
        {
            "ticker": "KX.ODM005.YES",
            "question": "Will ODM-005 fixture one resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 40,
            "model_probability": 54,
            "liquidity": 2500,
            "volume": 10000,
            "status": "open",
        },
        {
            "ticker": "KX.ODM005.NO",
            "question": "Will ODM-005 fixture two resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 76,
            "model_probability": 64,
            "liquidity": 3000,
            "volume": 15000,
            "status": "open",
        },
        {
            "ticker": "KX.ODM005.REJECT",
            "question": "Will ODM-005 low-edge fixture resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 50,
            "model_probability": 50.5,
            "liquidity": 3000,
            "status": "open",
        },
    ]

    bridge = PredictionMarketDiscoveryRegistryBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_and_bridge(
        raw_markets,
        source_name="odm_005_test_source",
        min_edge=0.02,
        min_liquidity=100,
    )
    report_b = bridge.discover_and_bridge(
        list(reversed(raw_markets)),
        source_name="odm_005_test_source",
        min_edge=0.02,
        min_liquidity=100,
    )

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "ODM-005"
    assert report_a.bridge_id == "oracle.discovery.bridge.prediction_market_registry"
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
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.payload["universal_market"]["market_type"] == "prediction_market"

    try:
        first.payload["read_only"] = False
        raise AssertionError("registry payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "ODM-005"
    assert d["read_only"] is True
    assert d["telemetry"]["opportunities_seen"] == 2
    assert d["telemetry"]["records_emitted"] == 2
    assert d["telemetry"]["read_only"] is True

    print("[PASS] ODM-005 Prediction Market Discovery Registry Bridge")
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
    test_odm_005_prediction_market_discovery_registry_bridge()
