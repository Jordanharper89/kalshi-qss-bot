
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_discovery_engine import (
    discover_liquidity_opportunities,
)
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_pipeline_gate import (
    validate_liquidity_discovery_result,
)
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_registry_bridge import (
    LiquidityRegistryBridge,
    bridge_liquidity_registry,
)


def _build_gate():
    raw = [
        {
            "market_id": "KXTHIN",
            "venue": "kalshi",
            "asset": "binary_event",
            "bid_price": 0.40,
            "ask_price": 0.48,
            "bid_depth": 100,
            "ask_depth": 50,
            "volume_24h": 12000,
            "open_interest": 50000,
            "observed_at": "2026-07-09T00:00:00+00:00",
        }
    ]
    result = discover_liquidity_opportunities(
        raw,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        min_spread_bps=250,
        max_total_depth=1000,
        min_depth_imbalance=0.30,
    )
    return validate_liquidity_discovery_result(result)


def test_liquidity_registry_bridge_registers_valid_gate():
    gate = _build_gate()
    bridge = LiquidityRegistryBridge()

    assert bridge.assert_read_only() is True

    entry = bridge.bridge(gate)

    assert entry.schema_version == "LQD-005"
    assert entry.engine_id == "oracle.discovery.liquidity.registry_bridge"
    assert entry.family == "liquidity_discovery"
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


def test_liquidity_registry_bridge_is_replayable():
    gate = _build_gate()

    entry1 = bridge_liquidity_registry(gate)
    entry2 = bridge_liquidity_registry(gate)

    assert entry1.registry_key == entry2.registry_key
    assert entry1.registry_hash == entry2.registry_hash


def test_liquidity_registry_bridge_accepts_empty_valid_gate():
    result = discover_liquidity_opportunities(
        [],
        source_name="liquidity.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    gate = validate_liquidity_discovery_result(result)
    entry = bridge_liquidity_registry(gate)

    assert entry.bridge_status == "registered"
    assert entry.accepted is True
    assert entry.opportunity_count == 0
    assert entry.read_only is True


if __name__ == "__main__":
    test_liquidity_registry_bridge_registers_valid_gate()
    test_liquidity_registry_bridge_is_replayable()
    test_liquidity_registry_bridge_accepts_empty_valid_gate()

    gate = _build_gate()
    entry = bridge_liquidity_registry(gate)

    print("[PASS] LQD-005 Liquidity Registry Bridge")
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
