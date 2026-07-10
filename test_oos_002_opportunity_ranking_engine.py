from qseries_v2.oracle_intelligence.opportunity_operating_system import build_oos
from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_ranking_engine import (
    OOS_RANKING_VERSION,
    RankingProfile,
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
        title="Will BTC close above 100k?",
        bid=0.52,
        ask=0.55,
        liquidity=30000,
    )


def _scalp(name="KXBTC-YES", edge=0.12, confidence=0.84, liquidity=0.76, risk=0.31, urgency=0.5, freshness=1.0, capital=None):
    market = _prediction_market(name)
    fair_value = 0.55 + edge

    return UniversalOpportunityFactory.prediction_market_scalp(
        market=market,
        fair_value=fair_value,
        market_price=0.55,
        confidence=confidence,
        explanation=f"Test scalp {name}",
        liquidity_score=liquidity,
        risk_score=risk,
        time_window=OpportunityTimeWindow(urgency_score=urgency, freshness_score=freshness),
        execution=OpportunityExecutionProfile(
            required_execution_adapter="prediction_market",
            execution_difficulty=0.25,
            capital_required=capital,
        ),
    )


def test_oos_002_scores_single_opportunity():
    engine = build_ranking_engine()
    opportunity = _scalp()

    breakdown = engine.score(opportunity)

    assert breakdown.schema_version == OOS_RANKING_VERSION
    assert breakdown.read_only is True
    assert breakdown.normalized_score > 0
    assert breakdown.profile == "balanced"


def test_oos_002_deterministic_ranking_order():
    engine = build_ranking_engine()

    low = _scalp("LOW", edge=0.04, confidence=0.60, liquidity=0.30, risk=0.60)
    high = _scalp("HIGH", edge=0.20, confidence=0.90, liquidity=0.80, risk=0.20)
    mid = _scalp("MID", edge=0.10, confidence=0.75, liquidity=0.60, risk=0.35)

    result = engine.rank([low, high, mid])

    assert result.schema_version == OOS_RANKING_VERSION
    assert result.read_only is True
    assert result.ranked_count == 3
    assert result.opportunities[0].opportunity.market_id == "HIGH"
    assert result.opportunities[1].opportunity.market_id == "MID"
    assert result.opportunities[2].opportunity.market_id == "LOW"


def test_oos_002_limit_and_serialization():
    engine = build_ranking_engine()

    result = engine.rank(
        [
            _scalp("A", edge=0.05),
            _scalp("B", edge=0.10),
            _scalp("C", edge=0.15),
        ],
        limit=2,
    )

    data = result.to_dict()

    assert result.ranked_count == 2
    assert data["schema_version"] == OOS_RANKING_VERSION
    assert data["read_only"] is True
    assert len(data["opportunities"]) == 2
    assert data["opportunities"][0]["rank"] == 1


def test_oos_002_profile_selection_changes_priority():
    engine = build_ranking_engine()

    high_edge_high_risk = _scalp("HIGH_EDGE_HIGH_RISK", edge=0.35, confidence=0.70, liquidity=0.50, risk=0.95)
    low_edge_low_risk = _scalp("LOW_EDGE_LOW_RISK", edge=0.08, confidence=0.88, liquidity=0.80, risk=0.05)

    ev_result = engine.rank(
        [high_edge_high_risk, low_edge_low_risk],
        profile=RankingProfile.MAX_EXPECTED_VALUE,
    )
    risk_result = engine.rank(
        [high_edge_high_risk, low_edge_low_risk],
        profile=RankingProfile.LOWEST_RISK,
    )

    assert ev_result.profile == "max_expected_value"
    assert risk_result.profile == "lowest_risk"
    assert ev_result.opportunities[0].opportunity.market_id == "HIGH_EDGE_HIGH_RISK"
    assert risk_result.opportunities[0].opportunity.market_id == "LOW_EDGE_LOW_RISK"


def test_oos_002_fastest_scalp_prefers_urgency_and_freshness():
    engine = build_ranking_engine()

    stale = _scalp("STALE", edge=0.20, confidence=0.85, urgency=0.10, freshness=0.20)
    fresh = _scalp("FRESH", edge=0.12, confidence=0.80, urgency=0.95, freshness=1.00)

    result = engine.rank([stale, fresh], profile=RankingProfile.FASTEST_SCALP)

    assert result.profile == "fastest_scalp"
    assert result.opportunities[0].opportunity.market_id == "FRESH"


def test_oos_002_capital_efficient_penalizes_large_capital():
    engine = build_ranking_engine()

    large_cap = _scalp("LARGE_CAP", edge=0.18, confidence=0.86, liquidity=0.80, risk=0.20, capital=25000)
    small_cap = _scalp("SMALL_CAP", edge=0.16, confidence=0.84, liquidity=0.80, risk=0.20, capital=50)

    result = engine.rank([large_cap, small_cap], profile=RankingProfile.CAPITAL_EFFICIENT)

    assert result.profile == "capital_efficient"
    assert result.opportunities[0].opportunity.market_id == "SMALL_CAP"


def test_oos_002_rank_oos_active_records():
    oos = build_oos()
    engine = build_ranking_engine()

    a = _scalp("A", edge=0.05)
    b = _scalp("B", edge=0.20)

    ia = oos.intake(a)
    oos.intake(b)

    oos.transition(ia.fingerprint, "verified")
    oos.transition(ia.fingerprint, "ranked")
    oos.transition(ia.fingerprint, "assigned")
    oos.transition(ia.fingerprint, "executed")
    oos.transition(ia.fingerprint, "archived")

    result = engine.rank_oos(oos, active_only=True)

    assert result.ranked_count == 1
    assert result.opportunities[0].opportunity.market_id == "B"


def test_oos_002_rejects_non_read_only_objects():
    class BadOpportunity:
        read_only = False

        def fingerprint(self):
            return "bad"

        def to_dict(self):
            return {}

    engine = build_ranking_engine()

    try:
        engine.rank([BadOpportunity()])
        raise AssertionError("Ranking should reject non-read-only opportunity.")
    except ValueError:
        pass


if __name__ == "__main__":
    test_oos_002_scores_single_opportunity()
    test_oos_002_deterministic_ranking_order()
    test_oos_002_limit_and_serialization()
    test_oos_002_profile_selection_changes_priority()
    test_oos_002_fastest_scalp_prefers_urgency_and_freshness()
    test_oos_002_capital_efficient_penalizes_large_capital()
    test_oos_002_rank_oos_active_records()
    test_oos_002_rejects_non_read_only_objects()

    engine = build_ranking_engine()
    result = engine.rank(
        [
            _scalp("LOW", edge=0.04, confidence=0.60, liquidity=0.30, risk=0.60),
            _scalp("HIGH", edge=0.20, confidence=0.90, liquidity=0.80, risk=0.20),
            _scalp("MID", edge=0.10, confidence=0.75, liquidity=0.60, risk=0.35),
        ]
    )

    print("[PASS] OOS-002 Opportunity Ranking Engine")
    print(
        {
            "schema_version": result.schema_version,
            "profile": result.profile,
            "ranked_count": result.ranked_count,
            "top_market": result.opportunities[0].opportunity.market_id,
            "top_score": result.opportunities[0].score,
            "read_only": result.read_only,
        }
    )
