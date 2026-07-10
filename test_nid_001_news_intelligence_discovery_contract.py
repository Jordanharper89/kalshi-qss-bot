
from qseries_v2.oracle_intelligence.news_intelligence_discovery_model.news_intelligence_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    NewsIntelligenceFamily,
    NewsIntelligenceDiscoveryRequest,
    EmptyNewsIntelligenceDiscoveryEngine,
)


def test_nid_001_news_intelligence_discovery_contract():
    request = NewsIntelligenceDiscoveryRequest(
        request_id="news.intelligence.discovery.test.request",
        family=NewsIntelligenceFamily.MARKET_MOVING_NEWS,
        source_name="test_source",
        article_ids=("article_a", "article_b"),
        topics=("Fed", "inflation"),
        markets=("rates", "prediction_markets"),
        metadata={"records": [{"article_id": "article_a", "topic": "fed"}]},
    )

    engine = EmptyNewsIntelligenceDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "NID-001"
    assert CONTRACT_ID == "oracle.discovery.contract.news_intelligence"

    assert request.read_only is True
    assert request.article_ids == ("article_a", "article_b")
    assert request.topics == ("fed", "inflation")
    assert request.markets == ("RATES", "PREDICTION_MARKETS")
    assert request.family == NewsIntelligenceFamily.MARKET_MOVING_NEWS

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.supports_replay is True
    assert caps.telemetry is True
    assert caps.metadata["execution"] is False
    assert caps.metadata["order_allowed"] is False
    assert caps.metadata["position_sizing_allowed"] is False

    assert health.status == "ok"
    assert health.ready is True
    assert health.read_only is True

    assert result.schema_version == "NID-001"
    assert result.engine_id == "oracle.discovery.news_intelligence.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.articles_seen == 0
    assert result.telemetry.opportunities_emitted == 0

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "NID-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] NID-001 News Intelligence Discovery Contract")
    print({
        "schema_version": d["schema_version"],
        "engine_id": d["engine_id"],
        "status": d["status"],
        "opportunities": len(d["opportunities"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_nid_001_news_intelligence_discovery_contract()
