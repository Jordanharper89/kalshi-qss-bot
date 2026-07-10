
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_discovery_engine import (
    discover_volatility_opportunities,
)
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_pipeline_gate import (
    validate_volatility_discovery_result,
)
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_registry_bridge import (
    VolatilityRegistryBridge,
    bridge_volatility_registry,
)


def _build_gate():
    raw = [
        {
            "market_id": "KXVOL-EXPAND",
            "venue": "kalshi",
            "asset": "binary_event",
            "realized_volatility": 0.42,
            "implied_volatility": 0.20,
            "baseline_volatility": 0.20,
            "price_change": 0.08,
            "volume": 12000,
            "window": "1d",
            "observed_at": "2026-07-09T00:00:00+00:00",
        }
    ]
    result = discover_volatility_opportunities(
        raw,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    return validate_volatility_discovery_result(result)


def test_volatility_registry_bridge_registers_valid_gate():
    gate = _build_gate()
    bridge = VolatilityRegistryBridge()

    assert bridge.assert_read_only() is True

    entry = bridge.bridge(gate)

    assert entry.schema_version == "VLD-005"
    assert entry.engine_id == "oracle.discovery.volatility.registry_bridge"
    assert entry.family == "volatility_discovery"
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


def test_volatility_registry_bridge_is_replayable():
    gate = _build_gate()

    entry1 = bridge_volatility_registry(gate)
    entry2 = bridge_volatility_registry(gate)

    assert entry1.registry_key == entry2.registry_key
    assert entry1.registry_hash == entry2.registry_hash


def test_volatility_registry_bridge_accepts_empty_valid_gate():
    result = discover_volatility_opportunities(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    gate = validate_volatility_discovery_result(result)
    entry = bridge_volatility_registry(gate)

    assert entry.bridge_status == "registered"
    assert entry.accepted is True
    assert entry.opportunity_count == 0
    assert entry.read_only is True


if __name__ == "__main__":
    test_volatility_registry_bridge_registers_valid_gate()
    test_volatility_registry_bridge_is_replayable()
    test_volatility_registry_bridge_accepts_empty_valid_gate()

    gate = _build_gate()
    entry = bridge_volatility_registry(gate)

    print("[PASS] VLD-005 Volatility Registry Bridge")
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
