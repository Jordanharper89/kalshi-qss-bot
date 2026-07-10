
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_oos_runtime_gate import (
    VolatilityOOSRuntimeGate,
    run_volatility_oos_runtime_gate,
    validate_volatility_oos_runtime,
)
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_pipeline_bridge import (
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
    }
]


def test_volatility_oos_runtime_gate_accepts_valid_pipeline():
    pipeline = run_volatility_pipeline(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gate = VolatilityOOSRuntimeGate()
    assert gate.assert_read_only() is True

    result = gate.validate(
        pipeline,
        runtime_context={"mode": "oos", "fold": "test-fold-001"},
    )

    assert result.schema_version == "VLD-007"
    assert result.engine_id == "oracle.discovery.volatility.oos_runtime_gate"
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.read_only is True
    assert result.pipeline_hash == pipeline.pipeline_hash
    assert result.opportunity_count == pipeline.opportunity_count
    assert result.checks["no_execution_context"] is True
    assert result.oos_hash


def test_volatility_oos_runtime_gate_rejects_execution_context():
    pipeline = run_volatility_pipeline(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    result = validate_volatility_oos_runtime(
        pipeline,
        runtime_context={"mode": "oos", "execute": True},
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert result.checks["no_execution_context"] is False
    assert result.read_only is True


def test_volatility_oos_runtime_gate_is_replayable():
    r1 = run_volatility_oos_runtime_gate(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "replay", "fold": "A"},
    )
    r2 = run_volatility_oos_runtime_gate(
        list(reversed(RAW)),
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"fold": "A", "mode": "replay"},
    )

    assert r1.oos_hash == r2.oos_hash


def test_volatility_oos_runtime_gate_accepts_empty_pipeline():
    result = run_volatility_oos_runtime_gate(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "shadow"},
    )

    assert result.status == "accepted"
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.read_only is True


if __name__ == "__main__":
    test_volatility_oos_runtime_gate_accepts_valid_pipeline()
    test_volatility_oos_runtime_gate_rejects_execution_context()
    test_volatility_oos_runtime_gate_is_replayable()
    test_volatility_oos_runtime_gate_accepts_empty_pipeline()

    result = run_volatility_oos_runtime_gate(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )

    print("[PASS] VLD-007 Volatility OOS Runtime Gate")
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
