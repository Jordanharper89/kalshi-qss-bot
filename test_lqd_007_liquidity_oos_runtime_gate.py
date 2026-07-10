
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_oos_runtime_gate import (
    LiquidityOOSRuntimeGate,
    run_liquidity_oos_runtime_gate,
    validate_liquidity_oos_runtime,
)
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_pipeline_bridge import (
    run_liquidity_pipeline,
)


RAW = [
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


def test_liquidity_oos_runtime_gate_accepts_valid_pipeline():
    pipeline = run_liquidity_pipeline(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        min_spread_bps=250,
        max_total_depth=1000,
        min_depth_imbalance=0.30,
    )

    gate = LiquidityOOSRuntimeGate()
    assert gate.assert_read_only() is True

    result = gate.validate(
        pipeline,
        runtime_context={"mode": "oos", "fold": "test-fold-001"},
    )

    assert result.schema_version == "LQD-007"
    assert result.engine_id == "oracle.discovery.liquidity.oos_runtime_gate"
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.read_only is True
    assert result.pipeline_hash == pipeline.pipeline_hash
    assert result.opportunity_count == pipeline.opportunity_count
    assert result.checks["no_execution_context"] is True
    assert result.oos_hash


def test_liquidity_oos_runtime_gate_rejects_execution_context():
    pipeline = run_liquidity_pipeline(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        min_spread_bps=250,
        max_total_depth=1000,
        min_depth_imbalance=0.30,
    )

    result = validate_liquidity_oos_runtime(
        pipeline,
        runtime_context={"mode": "oos", "execute": True},
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert result.checks["no_execution_context"] is False
    assert result.read_only is True


def test_liquidity_oos_runtime_gate_is_replayable():
    r1 = run_liquidity_oos_runtime_gate(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "replay", "fold": "A"},
    )
    r2 = run_liquidity_oos_runtime_gate(
        list(reversed(RAW)),
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"fold": "A", "mode": "replay"},
    )

    assert r1.oos_hash == r2.oos_hash


def test_liquidity_oos_runtime_gate_accepts_empty_pipeline():
    result = run_liquidity_oos_runtime_gate(
        [],
        source_name="liquidity.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "shadow"},
    )

    assert result.status == "accepted"
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.read_only is True


if __name__ == "__main__":
    test_liquidity_oos_runtime_gate_accepts_valid_pipeline()
    test_liquidity_oos_runtime_gate_rejects_execution_context()
    test_liquidity_oos_runtime_gate_is_replayable()
    test_liquidity_oos_runtime_gate_accepts_empty_pipeline()

    result = run_liquidity_oos_runtime_gate(
        [],
        source_name="liquidity.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )

    print("[PASS] LQD-007 Liquidity OOS Runtime Gate")
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
