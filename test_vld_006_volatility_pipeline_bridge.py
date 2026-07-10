
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_pipeline_bridge import (
    VolatilityPipelineBridge,
    run_volatility_pipeline,
)


RAW = [
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
    },
    {
        "market_id": "KXVOL-CONTRACT",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.10,
        "implied_volatility": 0.24,
        "baseline_volatility": 0.20,
        "price_change": 0.01,
        "volume": 9000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_volatility_pipeline_bridge_runs_full_pipeline():
    bridge = VolatilityPipelineBridge(source_name="volatility.test")

    assert bridge.assert_read_only() is True

    result = bridge.run(
        RAW,
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.schema_version == "VLD-006"
    assert result.engine_id == "oracle.discovery.volatility.pipeline_bridge"
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.read_only is True
    assert result.opportunity_count >= 4
    assert result.discovery.schema_version == "VLD-003"
    assert result.gate.schema_version == "VLD-004"
    assert result.registry_entry.schema_version == "VLD-005"
    assert result.gate.accepted is True
    assert result.registry_entry.accepted is True
    assert result.pipeline_hash
    assert result.audit["read_only"] is True
    assert result.audit["deterministic"] is True


def test_volatility_pipeline_bridge_is_replayable_and_order_independent():
    result1 = run_volatility_pipeline(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    result2 = run_volatility_pipeline(
        list(reversed(RAW)),
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result1.pipeline_hash == result2.pipeline_hash
    assert result1.discovery.result_hash == result2.discovery.result_hash
    assert result1.gate.gate_hash == result2.gate.gate_hash
    assert result1.registry_entry.registry_hash == result2.registry_entry.registry_hash


def test_volatility_pipeline_bridge_accepts_empty_valid_pipeline():
    result = run_volatility_pipeline(
        [],
        source_name="volatility.empty",
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
    test_volatility_pipeline_bridge_runs_full_pipeline()
    test_volatility_pipeline_bridge_is_replayable_and_order_independent()
    test_volatility_pipeline_bridge_accepts_empty_valid_pipeline()

    result = run_volatility_pipeline(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    print("[PASS] VLD-006 Volatility Pipeline Bridge")
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
