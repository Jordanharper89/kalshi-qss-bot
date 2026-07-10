
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_pipeline_bridge import (
    LiquidityPipelineBridge,
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
    },
    {
        "market_id": "KXDEEP",
        "venue": "kalshi",
        "asset": "binary_event",
        "bid_price": 0.49,
        "ask_price": 0.50,
        "bid_depth": 5000,
        "ask_depth": 5200,
        "volume_24h": 50000,
        "open_interest": 100000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_liquidity_pipeline_bridge_runs_full_pipeline():
    bridge = LiquidityPipelineBridge(
        source_name="liquidity.test",
        min_spread_bps=250,
        max_total_depth=1000,
        min_depth_imbalance=0.30,
    )

    assert bridge.assert_read_only() is True

    result = bridge.run(
        RAW,
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.schema_version == "LQD-006"
    assert result.engine_id == "oracle.discovery.liquidity.pipeline_bridge"
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.read_only is True
    assert result.opportunity_count >= 2
    assert result.discovery.schema_version == "LQD-003"
    assert result.gate.schema_version == "LQD-004"
    assert result.registry_entry.schema_version == "LQD-005"
    assert result.gate.accepted is True
    assert result.registry_entry.accepted is True
    assert result.pipeline_hash
    assert result.audit["read_only"] is True
    assert result.audit["deterministic"] is True


def test_liquidity_pipeline_bridge_is_replayable_and_order_independent():
    result1 = run_liquidity_pipeline(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        min_spread_bps=250,
        max_total_depth=1000,
        min_depth_imbalance=0.30,
    )
    result2 = run_liquidity_pipeline(
        list(reversed(RAW)),
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        min_spread_bps=250,
        max_total_depth=1000,
        min_depth_imbalance=0.30,
    )

    assert result1.pipeline_hash == result2.pipeline_hash
    assert result1.discovery.result_hash == result2.discovery.result_hash
    assert result1.gate.gate_hash == result2.gate.gate_hash
    assert result1.registry_entry.registry_hash == result2.registry_entry.registry_hash


def test_liquidity_pipeline_bridge_accepts_empty_valid_pipeline():
    result = run_liquidity_pipeline(
        [],
        source_name="liquidity.empty",
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
    test_liquidity_pipeline_bridge_runs_full_pipeline()
    test_liquidity_pipeline_bridge_is_replayable_and_order_independent()
    test_liquidity_pipeline_bridge_accepts_empty_valid_pipeline()

    result = run_liquidity_pipeline(
        [],
        source_name="liquidity.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    print("[PASS] LQD-006 Liquidity Pipeline Bridge")
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
