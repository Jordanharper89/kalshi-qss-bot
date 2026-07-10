
from dataclasses import replace

from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_discovery_engine import (
    discover_correlation_opportunities,
)
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_pipeline_gate import (
    validate_correlation_discovery_result,
)
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_registry_bridge import (
    CorrelationRegistryBridge,
    bridge_correlation_registry,
)


RAW = [
    {
        "primary_market_id": "KXTEST-A",
        "related_market_id": "KXTEST-B",
        "venue": "kalshi",
        "correlation": 0.82,
        "baseline_correlation": 0.80,
        "recent_correlation": 0.20,
        "lag": 0,
        "window": "30d",
        "sample_size": 120,
        "primary_return": 0.06,
        "related_return": -0.01,
        "observed_at": (
            "2026-07-09T00:00:00+00:00"
        ),
    },
    {
        "primary_market_id": "KXTEST-C",
        "related_market_id": "KXTEST-D",
        "venue": "kalshi",
        "correlation": -0.76,
        "baseline_correlation": -0.72,
        "recent_correlation": 0.31,
        "lag": 2,
        "window": "30d",
        "sample_size": 150,
        "primary_return": -0.03,
        "related_return": 0.04,
        "observed_at": (
            "2026-07-09T00:00:00+00:00"
        ),
    },
]


def _build_gate():
    discovery = discover_correlation_opportunities(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    return validate_correlation_discovery_result(
        discovery
    )


def test_correlation_registry_bridge_registers_valid_gate():
    gate = _build_gate()
    bridge = CorrelationRegistryBridge()

    assert bridge.assert_read_only() is True

    entry = bridge.bridge(gate)

    assert entry.schema_version == "CRD-005"
    assert (
        entry.engine_id
        == "oracle.discovery.correlation.registry_bridge"
    )
    assert entry.family == "correlation_discovery"
    assert entry.bridge_status == "registered"
    assert entry.accepted is True
    assert entry.read_only is True
    assert entry.source_gate_hash == gate.gate_hash
    assert (
        entry.source_result_hash
        == gate.discovery_result_hash
    )
    assert (
        entry.opportunity_count
        == gate.opportunity_count
    )
    assert entry.registry_key
    assert entry.registry_hash

    assert (
        entry.capabilities["deterministic"]
        is True
    )
    assert (
        entry.capabilities["replayable"]
        is True
    )
    assert (
        entry.capabilities["immutable"]
        is True
    )
    assert (
        entry.capabilities["read_only"]
        is True
    )
    assert (
        entry.capabilities["execution_capable"]
        is False
    )
    assert (
        entry.capabilities[
            "external_mutation_allowed"
        ]
        is False
    )


def test_correlation_registry_bridge_is_replayable():
    gate = _build_gate()

    entry1 = bridge_correlation_registry(gate)
    entry2 = bridge_correlation_registry(gate)

    assert (
        entry1.registry_key
        == entry2.registry_key
    )
    assert (
        entry1.registry_hash
        == entry2.registry_hash
    )
    assert (
        entry1.capabilities
        == entry2.capabilities
    )


def test_correlation_registry_bridge_accepts_empty_valid_gate():
    discovery = discover_correlation_opportunities(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    gate = validate_correlation_discovery_result(
        discovery
    )
    entry = bridge_correlation_registry(gate)

    assert entry.bridge_status == "registered"
    assert entry.accepted is True
    assert entry.opportunity_count == 0
    assert entry.read_only is True
    assert entry.registry_key
    assert entry.registry_hash


def test_correlation_registry_bridge_records_rejected_gate():
    gate = _build_gate()

    rejected_gate = replace(
        gate,
        status="rejected",
        accepted=False,
        reason="test rejection",
    )

    entry = bridge_correlation_registry(
        rejected_gate
    )

    assert entry.bridge_status == "rejected"
    assert entry.accepted is False
    assert entry.read_only is True
    assert entry.registry_key
    assert entry.registry_hash
    assert (
        entry.capabilities["source_accepted"]
        is False
    )


def test_correlation_registry_bridge_rejects_wrong_type():
    bridge = CorrelationRegistryBridge()

    try:
        bridge.bridge({"accepted": True})
    except TypeError as exc:
        assert str(exc) == (
            "gate_result must be a "
            "CorrelationPipelineGateResult"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid gate type"
        )


if __name__ == "__main__":
    test_correlation_registry_bridge_registers_valid_gate()
    test_correlation_registry_bridge_is_replayable()
    test_correlation_registry_bridge_accepts_empty_valid_gate()
    test_correlation_registry_bridge_records_rejected_gate()
    test_correlation_registry_bridge_rejects_wrong_type()

    discovery = discover_correlation_opportunities(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    gate = validate_correlation_discovery_result(
        discovery
    )
    entry = bridge_correlation_registry(gate)

    print(
        "[PASS] CRD-005 "
        "Correlation Registry Bridge"
    )
    print(
        {
            "schema_version": entry.schema_version,
            "engine_id": entry.engine_id,
            "bridge_status": entry.bridge_status,
            "accepted": entry.accepted,
            "opportunities": (
                entry.opportunity_count
            ),
            "read_only": entry.read_only,
        }
    )
