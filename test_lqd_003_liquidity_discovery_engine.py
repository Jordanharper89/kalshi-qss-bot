
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_discovery_engine import (
    LiquidityDiscoveryEngine,
    discover_liquidity_opportunities,
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


def test_liquidity_discovery_engine_detects_opportunities():
    engine = LiquidityDiscoveryEngine(
        min_spread_bps=250,
        max_total_depth=1000,
        min_depth_imbalance=0.30,
    )
    assert engine.assert_read_only() is True

    result = engine.discover_from_raw(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.schema_version == "LQD-003"
    assert result.engine_id == "oracle.discovery.liquidity.discovery_engine"
    assert result.status == "ok"
    assert result.read_only is True
    assert result.opportunity_count >= 2
    assert result.result_hash

    signal_types = sorted(set(o.signal_type for o in result.opportunities))
    assert "wide_spread" in signal_types
    assert "thin_depth" in signal_types
    assert "depth_imbalance" in signal_types

    for opportunity in result.opportunities:
        assert opportunity.opportunity_id
        assert opportunity.opportunity_hash
        assert 0.0 <= opportunity.confidence <= 1.0
        assert opportunity.magnitude >= 0.0
        assert "record_hash" in opportunity.evidence


def test_liquidity_discovery_engine_is_replayable_and_order_independent():
    result1 = discover_liquidity_opportunities(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        min_spread_bps=250,
        max_total_depth=1000,
        min_depth_imbalance=0.30,
    )
    result2 = discover_liquidity_opportunities(
        list(reversed(RAW)),
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        min_spread_bps=250,
        max_total_depth=1000,
        min_depth_imbalance=0.30,
    )

    assert result1.result_hash == result2.result_hash
    assert [o.opportunity_id for o in result1.opportunities] == [
        o.opportunity_id for o in result2.opportunities
    ]


def test_liquidity_discovery_engine_empty():
    result = discover_liquidity_opportunities(
        [],
        source_name="liquidity.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert result.result_hash


if __name__ == "__main__":
    test_liquidity_discovery_engine_detects_opportunities()
    test_liquidity_discovery_engine_is_replayable_and_order_independent()
    test_liquidity_discovery_engine_empty()

    result = discover_liquidity_opportunities(
        [],
        source_name="liquidity.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    print("[PASS] LQD-003 Liquidity Discovery Engine")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "opportunities": result.opportunity_count,
            "read_only": result.read_only,
        }
    )
