
from qseries_v2.oracle_intelligence.news_intelligence_discovery_model.news_intelligence_discovery_contract import (
    NewsIntelligenceDiscoveryRequest,
    NewsIntelligenceFamily,
)
from qseries_v2.oracle_intelligence.news_intelligence_discovery_model.news_intelligence_discovery_engine import (
    NewsIntelligenceDiscoveryEngine,
)


def test_nid_003_news_intelligence_discovery_engine():
    raw = [
        {
            "article_id": "article_b",
            "headline": "Fed signals slower cuts after inflation surprise",
            "publisher": "MarketWire",
            "link": "https://example.test/fed",
            "time": "2026-01-15T14:00:00Z",
            "category": "fed",
            "sentiment": "hawkish",
            "importance": "high",
            "relevance": 0.91,
            "markets": "RATES, EQUITIES, PREDICTION_MARKETS",
            "symbols": "FED, CPI",
        },
        {
            "id": "article_a",
            "title": "CPI comes in hotter than expected",
            "source": "EconomicDesk",
            "url": "https://example.test/cpi",
            "published_at": "2026-01-15T13:30:00Z",
            "topic": "inflation",
            "sentiment": "negative",
            "impact": "high",
            "relevance_score": 0.95,
            "affected_markets": ["RATES", "PREDICTION_MARKETS"],
            "entities": ["CPI", "USD"],
        },
        {
            "article_id": "article_minor",
            "title": "Local market commentary",
            "source": "SmallWire",
            "published_at": "2026-01-15T12:00:00Z",
            "topic": "local",
            "impact": "low",
            "relevance_score": 0.20,
            "affected_markets": ["LOCAL"],
        },
    ]

    request = NewsIntelligenceDiscoveryRequest(
        request_id="nid003.test.request",
        family=NewsIntelligenceFamily.MARKET_MOVING_NEWS,
        source_name="nid_003_test_feed",
        metadata={"raw_records": raw},
    )

    engine = NewsIntelligenceDiscoveryEngine(min_news_score=0.55)
    caps = engine.capabilities()
    health = engine.health()
    report_a = engine.discover(request)
    report_b = engine.discover(request)

    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.metadata["execution"] is False
    assert health.status == "ok"
    assert health.read_only is True

    assert report_a.schema_version == "NID-001"
    assert report_a.engine_id == "oracle.discovery.news_intelligence"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.opportunities) == 2
    assert [o.opportunity_id for o in report_a.opportunities] == [o.opportunity_id for o in report_b.opportunities]

    first = report_a.opportunities[0]
    assert first.read_only is True
    assert first.opportunity_type == "news_intelligence_signal"
    assert first.source_engine_id == "oracle.discovery.news_intelligence"
    assert first.news_score >= 0.55
    assert 0.0 <= first.confidence <= 1.0
    assert first.universal_market["market_type"] == "news_intelligence"
    assert first.universal_market["read_only"] is True
    assert first.universal_market["execution_allowed"] is False
    assert first.universal_market["order_allowed"] is False
    assert first.universal_market["position_sizing_allowed"] is False

    try:
        first.universal_market["execution_allowed"] = True
        raise AssertionError("universal_market should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["telemetry"]["records_seen"] == 3
    assert d["telemetry"]["articles_seen"] == 3
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["rejected_records"] == 1
    assert d["telemetry"]["read_only"] is True

    print("[PASS] NID-003.1 News Intelligence Discovery Engine Import Fix")
    print({
        "schema_version": "NID-003.1",
        "engine_id": d["engine_id"],
        "status": d["status"],
        "opportunities": len(d["opportunities"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_nid_003_news_intelligence_discovery_engine()
