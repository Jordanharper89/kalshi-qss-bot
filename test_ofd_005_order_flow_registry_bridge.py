
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_discovery_engine import (
    discover_order_flow_opportunities,
)
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_pipeline_gate import (
    validate_order_flow_discovery_result,
)
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_registry_bridge import (
    OrderFlowRegistryBridge,
    bridge_order_flow_registry,
)


def _build_gate():
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
    return validate_order_flow_discovery_result(result)


def test_order_flow_registry_bridge_registers_valid_gate():
    gate = _build_gate()
    bridge = OrderFlowRegistryBridge()

    assert bridge.assert_read_only() is True

    entry = bridge.bridge(gate)

    assert entry.schema_version == "OFD-005"
    assert entry.engine_id == "oracle.discovery.order_flow.registry_bridge"
    assert entry.family == "order_flow_discovery"
    assert entry.bridge_status == "registered"
    assert entry.accepted is True
    assert entry.read_only is True
    assert entry.source_gate_hash == gate.gate_hash
    assert entry.source_result_hash == gate.discovery_result_hash
    assert entry.opportunity_count == gate.opportunity_count
    assert entry.registry_key
    assert entry.registry_hash
    assert entry.capabilities["deterministic"] is True
    assert entry.capabilities["replayable"] is True
    assert entry.capabilities["read_only"] is True


def test_order_flow_registry_bridge_is_replayable():
    gate = _build_gate()

    entry1 = bridge_order_flow_registry(gate)
    entry2 = bridge_order_flow_registry(gate)

    assert entry1.registry_key == entry2.registry_key
    assert entry1.registry_hash == entry2.registry_hash


def test_order_flow_registry_bridge_accepts_empty_valid_gate():
    result = discover_order_flow_opportunities(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    gate = validate_order_flow_discovery_result(result)
    entry = bridge_order_flow_registry(gate)

    assert entry.bridge_status == "registered"
    assert entry.accepted is True
    assert entry.opportunity_count == 0
    assert entry.read_only is True


if __name__ == "__main__":
    test_order_flow_registry_bridge_registers_valid_gate()
    test_order_flow_registry_bridge_is_replayable()
    test_order_flow_registry_bridge_accepts_empty_valid_gate()

    gate = _build_gate()
    entry = bridge_order_flow_registry(gate)

    print("[PASS] OFD-005 Order Flow Registry Bridge")
    print(
        {
            "schema_version": entry.schema_version,
            "engine_id": entry.engine_id,
            "bridge_status": entry.bridge_status,
            "accepted": entry.accepted,
            "opportunities": entry.opportunity_count,
            "read_only": entry.read_only,
        }
    )
