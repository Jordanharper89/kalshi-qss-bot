from qseries_v2.oracle_intelligence.oracle_discovery_model.prediction_market_discovery_pipeline_bridge import (
    PredictionMarketDiscoveryPipelineBridge,
)


def test_odm_006_prediction_market_discovery_pipeline_bridge():
    raw_markets = [
        {
            "ticker": "KX.ODM006.YES",
            "question": "Will ODM-006 fixture one resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 40,
            "model_probability": 54,
            "liquidity": 2500,
            "volume": 10000,
            "status": "open",
        },
        {
            "ticker": "KX.ODM006.NO",
            "question": "Will ODM-006 fixture two resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 76,
            "model_probability": 64,
            "liquidity": 3000,
            "volume": 15000,
            "status": "open",
        },
        {
            "ticker": "KX.ODM006.REJECT",
            "question": "Will ODM-006 low-edge fixture resolve yes?",
            "platform": "kalshi",
            "category": "oracle_test",
            "price": 50,
            "model_probability": 50.5,
            "liquidity": 3000,
            "status": "open",
        },
    ]

    bridge = PredictionMarketDiscoveryPipelineBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_registry_and_bridge(
        raw_markets,
        source_name="odm_006_test_source",
        min_edge=0.02,
        min_liquidity=100,
    )
    report_b = bridge.discover_registry_and_bridge(
        list(reversed(raw_markets)),
        source_name="odm_006_test_source",
        min_edge=0.02,
        min_liquidity=100,
    )

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "ODM-006"
    assert report_a.bridge_id == "oracle.discovery.bridge.prediction_market_pipeline"
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
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["handoff_target"] == "OOS Opportunity Pipeline"

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("pipeline payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "ODM-006"
    assert d["read_only"] is True
    assert d["telemetry"]["records_seen"] == 2
    assert d["telemetry"]["packets_emitted"] == 2
    assert d["telemetry"]["read_only"] is True

    print("[PASS] ODM-006 Prediction Market Discovery Pipeline Bridge")
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
    test_odm_006_prediction_market_discovery_pipeline_bridge()
