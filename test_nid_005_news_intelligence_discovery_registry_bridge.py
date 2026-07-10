
from qseries_v2.oracle_intelligence.news_intelligence_discovery_model.news_intelligence_discovery_registry_bridge import (
    NewsIntelligenceDiscoveryRegistryBridge,
)


def test_nid_005_news_intelligence_discovery_registry_bridge():
    raw = [
        {"article_id": "article_b", "headline": "Fed signals slower cuts after inflation surprise", "publisher": "MarketWire", "link": "https://example.test/fed", "time": "2026-01-15T14:00:00Z", "category": "fed", "sentiment": "hawkish", "importance": "high", "relevance": 0.91, "markets": "RATES, EQUITIES, PREDICTION_MARKETS", "symbols": "FED, CPI"},
        {"id": "article_a", "title": "CPI comes in hotter than expected", "source": "EconomicDesk", "url": "https://example.test/cpi", "published_at": "2026-01-15T13:30:00Z", "topic": "inflation", "sentiment": "negative", "impact": "high", "relevance_score": 0.95, "affected_markets": ["RATES", "PREDICTION_MARKETS"], "entities": ["CPI", "USD"]},
        {"article_id": "article_minor", "title": "Local market commentary", "source": "SmallWire", "published_at": "2026-01-15T12:00:00Z", "topic": "local", "impact": "low", "relevance_score": 0.20, "affected_markets": ["LOCAL"]},
    ]

    bridge = NewsIntelligenceDiscoveryRegistryBridge()
    caps = bridge.capabilities()
    health = bridge.health()
    report_a = bridge.discover_and_bridge(raw, source_name="nid_005_test_source", min_news_score=0.55)
    report_b = bridge.discover_and_bridge(list(reversed(raw)), source_name="nid_005_test_source", min_news_score=0.55)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "NID-005"
    assert report_a.bridge_id == "oracle.discovery.bridge.news_intelligence_registry"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.records) == 2

    assert [r.registry_key for r in report_a.records] == [r.registry_key for r in report_b.records]

    first = report_a.records[0]
    assert first.read_only is True
    assert first.registry_status == "registry_ready"
    assert first.payload["read_only"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["order_allowed"] is False
    assert first.payload["position_sizing_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.payload["universal_market"]["market_type"] == "news_intelligence"

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("registry payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["telemetry"]["opportunities_seen"] == 2
    assert d["telemetry"]["records_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] NID-005 News Intelligence Discovery Registry Bridge")
    print({
        "schema_version": d["schema_version"],
        "bridge_id": d["bridge_id"],
        "status": d["status"],
        "records": len(d["records"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_nid_005_news_intelligence_discovery_registry_bridge()
