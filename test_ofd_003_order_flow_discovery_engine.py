
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_discovery_engine import (
    OrderFlowDiscoveryEngine,
    discover_order_flow_opportunities,
)


RAW = [
    {
        "market_id": "KXTEST-YES",
        "venue": "kalshi",
        "instrument": "binary_event",
        "bid_size": 80,
        "ask_size": 20,
        "bid_price": 0.42,
        "ask_price": 0.45,
        "last_price": 0.43,
        "volume": 2000,
        "open_interest": 7000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXTEST-NO",
        "venue": "kalshi",
        "instrument": "binary_event",
        "bid_size": 25,
        "ask_size": 75,
        "bid_price": 0.55,
        "ask_price": 0.58,
        "last_price": 0.56,
        "volume": 1800,
        "open_interest": 6000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXTEST-FLAT",
        "venue": "kalshi",
        "instrument": "binary_event",
        "bid_size": 51,
        "ask_size": 49,
        "volume": 1000,
        "open_interest": 3000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_order_flow_discovery_engine_detects_opportunities():
    engine = OrderFlowDiscoveryEngine(min_abs_imbalance=0.25)
    assert engine.assert_read_only() is True

    result = engine.discover_from_raw(
        RAW,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.schema_version == "OFD-003"
    assert result.engine_id == "oracle.discovery.order_flow.discovery_engine"
    assert result.status == "ok"
    assert result.read_only is True
    assert result.opportunity_count == 2
    assert result.result_hash

    directions = sorted(o.direction for o in result.opportunities)
    assert directions == ["ask_pressure", "bid_pressure"]

    for opportunity in result.opportunities:
        assert opportunity.opportunity_id
        assert opportunity.opportunity_hash
        assert 0.0 <= opportunity.confidence <= 1.0
        assert opportunity.magnitude >= 0.25
        assert "record_hash" in opportunity.evidence


def test_order_flow_discovery_engine_is_replayable_and_order_independent():
    result1 = discover_order_flow_opportunities(
        RAW,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    result2 = discover_order_flow_opportunities(
        list(reversed(RAW)),
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result1.result_hash == result2.result_hash
    assert [o.opportunity_id for o in result1.opportunities] == [
        o.opportunity_id for o in result2.opportunities
    ]


def test_order_flow_discovery_engine_empty():
    result = discover_order_flow_opportunities(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert result.result_hash


if __name__ == "__main__":
    test_order_flow_discovery_engine_detects_opportunities()
    test_order_flow_discovery_engine_is_replayable_and_order_independent()
    test_order_flow_discovery_engine_empty()

    result = discover_order_flow_opportunities(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    print("[PASS] OFD-003 Order Flow Discovery Engine")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "opportunities": result.opportunity_count,
            "read_only": result.read_only,
        }
    )
