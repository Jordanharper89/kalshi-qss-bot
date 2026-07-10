
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_discovery_engine import (
    CorrelationDiscoveryEngine,
    discover_correlation_opportunities,
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
        "observed_at": "2026-07-09T00:00:00+00:00",
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
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_correlation_discovery_engine_detects_opportunities():
    engine = CorrelationDiscoveryEngine(
        strong_correlation_threshold=0.70,
        correlation_break_threshold=0.30,
        return_divergence_threshold=0.04,
        min_sample_size=20,
    )

    assert engine.assert_read_only() is True

    result = engine.discover_from_raw(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.schema_version == "CRD-003"
    assert (
        result.engine_id
        == "oracle.discovery.correlation.discovery_engine"
    )
    assert result.status == "ok"
    assert result.read_only is True
    assert result.opportunity_count >= 5
    assert result.result_hash

    signal_types = sorted(
        set(
            opportunity.signal_type
            for opportunity in result.opportunities
        )
    )

    assert "correlation_break" in signal_types
    assert "correlation_sign_flip" in signal_types
    assert "return_divergence" in signal_types
    assert "lead_lag_relationship" in signal_types
    assert "correlation_decay" in signal_types

    for opportunity in result.opportunities:
        assert opportunity.opportunity_id
        assert opportunity.opportunity_hash
        assert 0.0 <= opportunity.confidence <= 1.0
        assert 0.0 <= opportunity.magnitude <= 1.0
        assert opportunity.relationship
        assert "record_hash" in opportunity.evidence


def test_correlation_discovery_engine_is_replayable_and_order_independent():
    result1 = discover_correlation_opportunities(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    result2 = discover_correlation_opportunities(
        list(reversed(RAW)),
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result1.result_hash == result2.result_hash
    assert [
        opportunity.opportunity_id
        for opportunity in result1.opportunities
    ] == [
        opportunity.opportunity_id
        for opportunity in result2.opportunities
    ]


def test_correlation_discovery_engine_respects_sample_size():
    result = discover_correlation_opportunities(
        [
            {
                "primary_market_id": "A",
                "related_market_id": "B",
                "venue": "demo",
                "correlation": 0.90,
                "baseline_correlation": 0.90,
                "recent_correlation": 0.10,
                "lag": 1,
                "window": "7d",
                "sample_size": 5,
                "primary_return": 0.10,
                "related_return": -0.10,
                "observed_at": "2026-07-09T00:00:00+00:00",
            }
        ],
        source_name="correlation.small_sample",
        observed_at="2026-07-09T00:00:00+00:00",
        min_sample_size=20,
    )

    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.read_only is True


def test_correlation_discovery_engine_empty():
    result = discover_correlation_opportunities(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert result.result_hash


if __name__ == "__main__":
    test_correlation_discovery_engine_detects_opportunities()
    test_correlation_discovery_engine_is_replayable_and_order_independent()
    test_correlation_discovery_engine_respects_sample_size()
    test_correlation_discovery_engine_empty()

    result = discover_correlation_opportunities(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    print("[PASS] CRD-003 Correlation Discovery Engine")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "opportunities": result.opportunity_count,
            "read_only": result.read_only,
        }
    )
