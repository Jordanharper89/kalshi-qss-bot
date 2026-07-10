
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_discovery_engine import (
    discover_liquidity_opportunities,
)
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_pipeline_gate import (
    LiquidityPipelineGate,
    validate_liquidity_discovery_result,
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


def test_liquidity_pipeline_gate_accepts_valid_result():
    result = discover_liquidity_opportunities(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        min_spread_bps=250,
        max_total_depth=1000,
        min_depth_imbalance=0.30,
    )

    gate = LiquidityPipelineGate()
    assert gate.assert_read_only() is True

    gated = gate.validate(result)

    assert gated.schema_version == "LQD-004"
    assert gated.engine_id == "oracle.discovery.liquidity.pipeline_gate"
    assert gated.status == "accepted"
    assert gated.accepted is True
    assert gated.read_only is True
    assert gated.discovery_result_hash == result.result_hash
    assert gated.opportunity_count == result.opportunity_count
    assert gated.gate_hash
    assert all(gated.checks.values())


def test_liquidity_pipeline_gate_accepts_empty_valid_result():
    result = discover_liquidity_opportunities(
        [],
        source_name="liquidity.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gated = validate_liquidity_discovery_result(result)

    assert gated.status == "accepted"
    assert gated.accepted is True
    assert gated.opportunity_count == 0
    assert all(gated.checks.values())


def test_liquidity_pipeline_gate_is_replayable():
    result = discover_liquidity_opportunities(
        [],
        source_name="liquidity.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gated1 = validate_liquidity_discovery_result(result)
    gated2 = validate_liquidity_discovery_result(result)

    assert gated1.gate_hash == gated2.gate_hash


if __name__ == "__main__":
    test_liquidity_pipeline_gate_accepts_valid_result()
    test_liquidity_pipeline_gate_accepts_empty_valid_result()
    test_liquidity_pipeline_gate_is_replayable()

    result = discover_liquidity_opportunities(
        [],
        source_name="liquidity.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    gated = validate_liquidity_discovery_result(result)

    print("[PASS] LQD-004 Liquidity Pipeline Gate")
    print(
        {
            "schema_version": gated.schema_version,
            "engine_id": gated.engine_id,
            "status": gated.status,
            "accepted": gated.accepted,
            "read_only": gated.read_only,
        }
    )
