
from qseries_v2.oracle_intelligence.social_intelligence_discovery_model.social_intelligence_discovery_contract import (
    SocialIntelligenceDiscoveryRequest,
    SocialIntelligenceFamily,
)
from qseries_v2.oracle_intelligence.social_intelligence_discovery_model.social_intelligence_discovery_engine import (
    SocialIntelligenceDiscoveryEngine,
)


def test_sid_003_social_intelligence_discovery_engine():
    raw = [
        {
            "post_id": "post_b",
            "platform": "X",
            "author": "macro_trader",
            "topic": "fed",
            "text": "Rate cut odds are collapsing after CPI reaction.",
            "posted_at": "2026-01-15T14:05:00Z",
            "sentiment": "bearish",
            "engagement_score": 0.88,
            "velocity_score": 0.82,
            "credibility_score": 0.80,
            "markets": "RATES, PREDICTION_MARKETS",
            "symbols": "FED, CPI",
        },
        {
            "id": "post_a",
            "network": "reddit",
            "username": "kalshi_watcher",
            "category": "prediction_market_social",
            "content": "Inflation markets are moving fast after the CPI headline.",
            "time": "2026-01-15T13:35:00Z",
            "sentiment": "bullish",
            "engagement": 0.91,
            "velocity": 0.87,
            "credibility": 0.76,
            "affected_markets": ["PREDICTION_MARKETS", "RATES"],
            "entities": ["CPI", "KALSHI"],
        },
        {
            "post_id": "post_minor",
            "platform": "x",
            "author": "small_account",
            "topic": "local",
            "text": "Random local market comment.",
            "posted_at": "2026-01-15T12:00:00Z",
            "sentiment": "neutral",
            "engagement_score": 0.10,
            "velocity_score": 0.10,
            "credibility_score": 0.20,
            "affected_markets": ["LOCAL"],
        },
    ]

    request = SocialIntelligenceDiscoveryRequest(
        request_id="sid003.test.request",
        family=SocialIntelligenceFamily.SOCIAL_MOMENTUM,
        source_name="sid_003_test_feed",
        metadata={"raw_records": raw},
    )

    engine = SocialIntelligenceDiscoveryEngine(min_social_score=0.55)
    caps = engine.capabilities()
    health = engine.health()
    report_a = engine.discover(request)
    report_b = engine.discover(request)

    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.metadata["execution"] is False
    assert caps.metadata["posting_allowed"] is False
    assert caps.metadata["dm_allowed"] is False
    assert health.status == "ok"
    assert health.read_only is True

    assert report_a.schema_version == "SID-001"
    assert report_a.engine_id == "oracle.discovery.social_intelligence"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.opportunities) == 2
    assert [o.opportunity_id for o in report_a.opportunities] == [o.opportunity_id for o in report_b.opportunities]

    first = report_a.opportunities[0]
    assert first.read_only is True
    assert first.opportunity_type == "social_intelligence_signal"
    assert first.source_engine_id == "oracle.discovery.social_intelligence"
    assert first.social_score >= 0.55
    assert 0.0 <= first.confidence <= 1.0
    assert first.universal_market["market_type"] == "social_intelligence"
    assert first.universal_market["read_only"] is True
    assert first.universal_market["execution_allowed"] is False
    assert first.universal_market["order_allowed"] is False
    assert first.universal_market["position_sizing_allowed"] is False
    assert first.universal_market["posting_allowed"] is False
    assert first.universal_market["dm_allowed"] is False

    try:
        first.universal_market["execution_allowed"] = True
        raise AssertionError("universal_market should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["telemetry"]["records_seen"] == 3
    assert d["telemetry"]["posts_seen"] == 3
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["rejected_records"] == 1
    assert d["telemetry"]["read_only"] is True

    print("[PASS] SID-003 Social Intelligence Discovery Engine")
    print({
        "schema_version": "SID-003",
        "engine_id": d["engine_id"],
        "status": d["status"],
        "opportunities": len(d["opportunities"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_sid_003_social_intelligence_discovery_engine()
