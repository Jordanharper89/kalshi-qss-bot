from qseries_v2.oracle_intelligence.opportunity_operating_system import build_oos
from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_pipeline import (
    OOS_PIPELINE_VERSION,
    OpportunityPipeline,
    build_pipeline,
)
from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_ranking_engine import (
    build_ranking_engine,
)
from qseries_v2.oracle_intelligence.universal_market_model import UniversalMarketFactory
from qseries_v2.oracle_intelligence.universal_opportunity_model import (
    OpportunityExecutionProfile,
    OpportunityTimeWindow,
    UniversalOpportunityFactory,
)


def _prediction_market(market_id="KXBTC-YES"):
    return UniversalMarketFactory.from_prediction_market(
        venue_id="kalshi",
        venue_name="Kalshi",
        market_id=market_id,
        title=f"Prediction market {market_id}",
        bid=0.52,
        ask=0.55,
        liquidity=30000,
    )


def _scalp(market_id="KXBTC-YES", edge=0.12, confidence=0.84, liquidity=0.76, risk=0.31):
    market = _prediction_market(market_id)
    return UniversalOpportunityFactory.prediction_market_scalp(
        market=market,
        fair_value=0.55 + edge,
        market_price=0.55,
        confidence=confidence,
        explanation=f"Oracle fair value gap for {market_id}.",
        liquidity_score=liquidity,
        risk_score=risk,
        time_window=OpportunityTimeWindow(urgency_score=0.50, freshness_score=1.0),
        execution=OpportunityExecutionProfile(
            required_execution_adapter="prediction_market",
            execution_difficulty=0.25,
            capital_required=100,
        ),
    )


def _settlement(market_id="KXSETTLE-YES"):
    market = _prediction_market(market_id)
    return UniversalOpportunityFactory.settlement_edge(
        market=market,
        payout_certainty=0.99,
        market_price=0.93,
        confidence=0.96,
        explanation="Settlement certainty exceeds market price.",
        liquidity_score=0.70,
        risk_score=0.15,
    )


def _arb():
    market = UniversalMarketFactory.from_arbitrage_pair(
        market_id="arb:btc:a:b",
        title="BTC cross-venue spread",
        venue_a="VenueA",
        venue_b="VenueB",
        asset="BTC",
        spread=0.018,
        liquidity=50000,
    )
    return UniversalOpportunityFactory.arbitrage_spread(
        market=market,
        spread=0.018,
        confidence=0.91,
        explanation="Cross-venue spread exceeds execution cost estimate.",
        liquidity_score=0.80,
        risk_score=0.20,
    )


def test_oos_003_processes_and_ranks_opportunities():
    pipeline = build_pipeline()
    opportunities = [
        _scalp("LOW", edge=0.04, confidence=0.60, liquidity=0.30, risk=0.60),
        _scalp("HIGH", edge=0.20, confidence=0.90, liquidity=0.80, risk=0.20),
        _scalp("MID", edge=0.10, confidence=0.75, liquidity=0.60, risk=0.35),
    ]

    result = pipeline.process(opportunities, source="test_engine")

    assert result.schema_version == OOS_PIPELINE_VERSION
    assert result.read_only is True
    assert result.status == "ok"
    assert result.input_count == 3
    assert result.registered_count == 3
    assert result.duplicate_count == 0
    assert result.ranked_count == 3
    assert result.ranking_result.opportunities[0].opportunity.market_id == "HIGH"


def test_oos_003_duplicate_handling():
    pipeline = build_pipeline()
    opportunity = _scalp("DUPLICATE", edge=0.12)

    first = pipeline.process([opportunity], source="engine_a")
    second = pipeline.process([opportunity], source="engine_b")

    assert first.registered_count == 1
    assert second.registered_count == 0
    assert second.duplicate_count == 1
    assert len(pipeline.oos.all_records()) == 1
    assert pipeline.oos.telemetry().duplicate_count == 1


def test_oos_003_ranked_feed_limit():
    pipeline = build_pipeline()
    pipeline.process(
        [
            _scalp("A", edge=0.05),
            _scalp("B", edge=0.20),
            _scalp("C", edge=0.10),
        ]
    )

    feed = pipeline.ranked_feed(limit=2)

    assert feed.ranked_count == 2
    assert feed.opportunities[0].rank == 1
    assert feed.opportunities[1].rank == 2


def test_oos_003_works_with_external_oos_and_ranking_engine():
    oos = build_oos()
    ranking_engine = build_ranking_engine()
    pipeline = OpportunityPipeline(oos=oos, ranking_engine=ranking_engine)

    result = pipeline.process([_settlement(), _arb()], source="multi_source")

    assert result.registered_count == 2
    assert len(oos.all_records()) == 2
    assert result.ranked_count == 2
    assert result.telemetry["oos_total_registered"] == 2


def test_oos_003_serialization_and_telemetry():
    pipeline = build_pipeline()
    pipeline.process([_scalp("SERIAL", edge=0.13)], source="serializer")

    data = pipeline.to_dict()
    telemetry = pipeline.telemetry()

    assert data["schema_version"] == OOS_PIPELINE_VERSION
    assert data["read_only"] is True
    assert telemetry["read_only"] is True
    assert telemetry["oos"]["total_registered"] == 1
    assert len(data["oos"]["records"]) == 1


def test_oos_003_rejects_non_read_only_objects():
    class BadOpportunity:
        read_only = False

        def fingerprint(self):
            return "bad"

        def to_dict(self):
            return {}

    pipeline = build_pipeline()

    try:
        pipeline.process([BadOpportunity()])
        raise AssertionError("Pipeline should reject non-read-only opportunity.")
    except ValueError:
        pass


def test_oos_003_profile_pass_through():
    pipeline = build_pipeline()

    high_edge = _scalp("HIGH_EDGE", edge=0.30, confidence=0.70, liquidity=0.50, risk=0.90)
    low_risk = _scalp("LOW_RISK", edge=0.08, confidence=0.88, liquidity=0.80, risk=0.05)

    ev_result = pipeline.process(
        [high_edge, low_risk],
        profile="max_expected_value",
    )

    risk_result = pipeline.ranked_feed(profile="lowest_risk")

    assert ev_result.ranking_result.profile == "max_expected_value"
    assert risk_result.profile == "lowest_risk"


if __name__ == "__main__":
    test_oos_003_processes_and_ranks_opportunities()
    test_oos_003_duplicate_handling()
    test_oos_003_ranked_feed_limit()
    test_oos_003_works_with_external_oos_and_ranking_engine()
    test_oos_003_serialization_and_telemetry()
    test_oos_003_rejects_non_read_only_objects()
    test_oos_003_profile_pass_through()

    pipeline = build_pipeline()
    result = pipeline.process(
        [
            _scalp("LOW", edge=0.04, confidence=0.60, liquidity=0.30, risk=0.60),
            _scalp("HIGH", edge=0.20, confidence=0.90, liquidity=0.80, risk=0.20),
            _scalp("MID", edge=0.10, confidence=0.75, liquidity=0.60, risk=0.35),
        ],
        source="test_engine",
    )

    print("[PASS] OOS-003 Opportunity Pipeline")
    print(
        {
            "schema_version": result.schema_version,
            "input_count": result.input_count,
            "registered_count": result.registered_count,
            "duplicate_count": result.duplicate_count,
            "ranked_count": result.ranked_count,
            "top_market": result.ranking_result.opportunities[0].opportunity.market_id,
            "read_only": result.read_only,
        }
    )
