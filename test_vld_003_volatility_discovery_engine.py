
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_discovery_engine import (
    VolatilityDiscoveryEngine,
    discover_volatility_opportunities,
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


def test_volatility_discovery_engine_detects_opportunities():
    engine = VolatilityDiscoveryEngine(
        expansion_ratio_threshold=1.5,
        contraction_ratio_threshold=0.7,
        iv_rv_gap_threshold=0.10,
        shock_return_threshold=0.05,
    )
    assert engine.assert_read_only() is True

    result = engine.discover_from_raw(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.schema_version == "VLD-003"
    assert result.engine_id == "oracle.discovery.volatility.discovery_engine"
    assert result.status == "ok"
    assert result.read_only is True
    assert result.opportunity_count >= 4
    assert result.result_hash

    signal_types = sorted(set(o.signal_type for o in result.opportunities))
    assert "volatility_expansion" in signal_types
    assert "volatility_contraction" in signal_types
    assert "iv_rv_divergence" in signal_types
    assert "shock_volatility" in signal_types

    for opportunity in result.opportunities:
        assert opportunity.opportunity_id
        assert opportunity.opportunity_hash
        assert 0.0 <= opportunity.confidence <= 1.0
        assert opportunity.magnitude >= 0.0
        assert "record_hash" in opportunity.evidence


def test_volatility_discovery_engine_is_replayable_and_order_independent():
    result1 = discover_volatility_opportunities(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    result2 = discover_volatility_opportunities(
        list(reversed(RAW)),
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result1.result_hash == result2.result_hash
    assert [o.opportunity_id for o in result1.opportunities] == [
        o.opportunity_id for o in result2.opportunities
    ]


def test_volatility_discovery_engine_empty():
    result = discover_volatility_opportunities(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert result.result_hash


if __name__ == "__main__":
    test_volatility_discovery_engine_detects_opportunities()
    test_volatility_discovery_engine_is_replayable_and_order_independent()
    test_volatility_discovery_engine_empty()

    result = discover_volatility_opportunities(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    print("[PASS] VLD-003 Volatility Discovery Engine")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "opportunities": result.opportunity_count,
            "read_only": result.read_only,
        }
    )
