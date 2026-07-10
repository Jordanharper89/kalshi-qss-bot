
from qseries_v2.oracle_intelligence.news_intelligence_discovery_model.news_intelligence_source_adapter import (
    NewsIntelligenceSourceAdapter,
)


def test_nid_002_news_intelligence_source_adapter():
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
            "description": "Fed commentary reprices rate-cut expectations.",
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
            "summary": "Inflation data surprised above consensus.",
        },
    ]

    adapter = NewsIntelligenceSourceAdapter(source_name="nid_002_test_feed")
    caps = adapter.capabilities()
    health = adapter.health()
    batch_a = adapter.normalize_batch(raw)
    batch_b = adapter.normalize_batch(list(reversed(raw)))

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert batch_a.schema_version == "NID-002"
    assert batch_a.adapter_id == "oracle.discovery.source.news_intelligence"
    assert batch_a.read_only is True
    assert len(batch_a.snapshots) == 2

    order_a = [s.article_id for s in batch_a.snapshots]
    order_b = [s.article_id for s in batch_b.snapshots]
    assert order_a == order_b
    assert order_a == ["article_a", "article_b"]

    first = batch_a.snapshots[0]
    assert first.article_id == "article_a"
    assert first.title == "CPI comes in hotter than expected"
    assert first.source == "economicdesk"
    assert first.topic == "inflation"
    assert first.sentiment == "negative"
    assert first.impact == "high"
    assert first.relevance_score == 0.95
    assert first.affected_markets == ("RATES", "PREDICTION_MARKETS")
    assert first.entities == ("CPI", "USD")
    assert first.read_only is True

    try:
        first.metadata["x"] = "mutation"
        raise AssertionError("metadata should be immutable")
    except TypeError:
        pass

    d = batch_a.to_dict()
    assert d["schema_version"] == "NID-002"
    assert d["telemetry"]["raw_records_seen"] == 2
    assert d["telemetry"]["snapshots_emitted"] == 2
    assert d["telemetry"]["articles_seen"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] NID-002 News Intelligence Source Adapter")
    print({
        "schema_version": d["schema_version"],
        "adapter_id": d["adapter_id"],
        "snapshots": len(d["snapshots"]),
        "articles_seen": d["telemetry"]["articles_seen"],
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_nid_002_news_intelligence_source_adapter()
