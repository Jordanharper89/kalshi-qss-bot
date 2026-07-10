
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_pipeline_bridge import (
    OrderFlowPipelineBridge,
    run_order_flow_pipeline,
)


RAW = [
    {
        "market_id": "KXTEST-YES",
        "venue": "kalshi",
        "instrument": "binary_event",
        "bid_size": 80,
        "ask_size": 20,
        "bid_price": 0.42,
        "ask_price": 0.45,
        "last_price": 0.43,
        "volume": 2000,
        "open_interest": 7000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXTEST-NO",
        "venue": "kalshi",
        "instrument": "binary_event",
        "bid_size": 20,
        "ask_size": 80,
        "bid_price": 0.55,
        "ask_price": 0.58,
        "last_price": 0.56,
        "volume": 1900,
        "open_interest": 6500,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_order_flow_pipeline_bridge_runs_full_pipeline():
    bridge = OrderFlowPipelineBridge(source_name="order_flow.test")

    assert bridge.assert_read_only() is True

    result = bridge.run(
        RAW,
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.schema_version == "OFD-006"
    assert result.engine_id == "oracle.discovery.order_flow.pipeline_bridge"
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.read_only is True
    assert result.opportunity_count == 2
    assert result.discovery.schema_version == "OFD-003"
    assert result.gate.schema_version == "OFD-004"
    assert result.registry_entry.schema_version == "OFD-005"
    assert result.gate.accepted is True
    assert result.registry_entry.accepted is True
    assert result.pipeline_hash
    assert result.audit["read_only"] is True
    assert result.audit["deterministic"] is True


def test_order_flow_pipeline_bridge_is_replayable_and_order_independent():
    result1 = run_order_flow_pipeline(
        RAW,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    result2 = run_order_flow_pipeline(
        list(reversed(RAW)),
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result1.pipeline_hash == result2.pipeline_hash
    assert result1.discovery.result_hash == result2.discovery.result_hash
    assert result1.gate.gate_hash == result2.gate.gate_hash
    assert result1.registry_entry.registry_hash == result2.registry_entry.registry_hash


def test_order_flow_pipeline_bridge_accepts_empty_valid_pipeline():
    result = run_order_flow_pipeline(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.status == "accepted"
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.discovery.status == "empty"
    assert result.gate.accepted is True
    assert result.registry_entry.accepted is True
    assert result.read_only is True
    assert result.pipeline_hash


if __name__ == "__main__":
    test_order_flow_pipeline_bridge_runs_full_pipeline()
    test_order_flow_pipeline_bridge_is_replayable_and_order_independent()
    test_order_flow_pipeline_bridge_accepts_empty_valid_pipeline()

    result = run_order_flow_pipeline(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    print("[PASS] OFD-006 Order Flow Pipeline Bridge")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted": result.accepted,
            "opportunities": result.opportunity_count,
            "read_only": result.read_only,
        }
    )
