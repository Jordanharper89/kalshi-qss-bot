
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_discovery_engine import (
    discover_order_flow_opportunities,
)
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_pipeline_gate import (
    OrderFlowPipelineGate,
    validate_order_flow_discovery_result,
)


def test_order_flow_pipeline_gate_accepts_valid_result():
    raw = [
        {
            "market_id": "KXTEST-YES",
            "venue": "kalshi",
            "instrument": "binary_event",
            "bid_size": 80,
            "ask_size": 20,
            "volume": 2000,
            "open_interest": 7000,
            "observed_at": "2026-07-09T00:00:00+00:00",
        }
    ]

    result = discover_order_flow_opportunities(
        raw,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gate = OrderFlowPipelineGate()
    assert gate.assert_read_only() is True

    gated = gate.validate(result)

    assert gated.schema_version == "OFD-004"
    assert gated.engine_id == "oracle.discovery.order_flow.pipeline_gate"
    assert gated.status == "accepted"
    assert gated.accepted is True
    assert gated.read_only is True
    assert gated.discovery_result_hash == result.result_hash
    assert gated.opportunity_count == result.opportunity_count
    assert gated.gate_hash


def test_order_flow_pipeline_gate_accepts_empty_valid_result():
    result = discover_order_flow_opportunities(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gated = validate_order_flow_discovery_result(result)

    assert gated.status == "accepted"
    assert gated.accepted is True
    assert gated.opportunity_count == 0
    assert all(gated.checks.values())


def test_order_flow_pipeline_gate_is_replayable():
    result = discover_order_flow_opportunities(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gated1 = validate_order_flow_discovery_result(result)
    gated2 = validate_order_flow_discovery_result(result)

    assert gated1.gate_hash == gated2.gate_hash


if __name__ == "__main__":
    test_order_flow_pipeline_gate_accepts_valid_result()
    test_order_flow_pipeline_gate_accepts_empty_valid_result()
    test_order_flow_pipeline_gate_is_replayable()

    result = discover_order_flow_opportunities(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    gated = validate_order_flow_discovery_result(result)

    print("[PASS] OFD-004 Order Flow Pipeline Gate")
    print(
        {
            "schema_version": gated.schema_version,
            "engine_id": gated.engine_id,
            "status": gated.status,
            "accepted": gated.accepted,
            "read_only": gated.read_only,
        }
    )
