
from qseries_v2.oracle_intelligence.social_intelligence_discovery_model.social_intelligence_source_adapter import (
    SocialIntelligenceSourceAdapter,
)


def test_sid_002_social_intelligence_source_adapter():
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
    ]

    adapter = SocialIntelligenceSourceAdapter(source_name="sid_002_test_feed")
    caps = adapter.capabilities()
    health = adapter.health()
    batch_a = adapter.normalize_batch(raw)
    batch_b = adapter.normalize_batch(list(reversed(raw)))

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert caps["posting_allowed"] is False
    assert caps["dm_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert batch_a.schema_version == "SID-002"
    assert batch_a.adapter_id == "oracle.discovery.source.social_intelligence"
    assert batch_a.read_only is True
    assert len(batch_a.snapshots) == 2

    order_a = [s.post_id for s in batch_a.snapshots]
    order_b = [s.post_id for s in batch_b.snapshots]
    assert order_a == order_b
    assert order_a == ["post_a", "post_b"]

    first = batch_a.snapshots[0]
    assert first.post_id == "post_a"
    assert first.platform == "reddit"
    assert first.author == "kalshi_watcher"
    assert first.topic == "prediction_market_social"
    assert first.sentiment == "bullish"
    assert first.engagement_score == 0.91
    assert first.velocity_score == 0.87
    assert first.credibility_score == 0.76
    assert first.affected_markets == ("PREDICTION_MARKETS", "RATES")
    assert first.entities == ("CPI", "KALSHI")
    assert first.read_only is True

    try:
        first.metadata["x"] = "mutation"
        raise AssertionError("metadata should be immutable")
    except TypeError:
        pass

    d = batch_a.to_dict()
    assert d["schema_version"] == "SID-002"
    assert d["telemetry"]["raw_records_seen"] == 2
    assert d["telemetry"]["snapshots_emitted"] == 2
    assert d["telemetry"]["posts_seen"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["posting_allowed"] is False

    print("[PASS] SID-002 Social Intelligence Source Adapter")
    print({
        "schema_version": d["schema_version"],
        "adapter_id": d["adapter_id"],
        "snapshots": len(d["snapshots"]),
        "posts_seen": d["telemetry"]["posts_seen"],
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_sid_002_social_intelligence_source_adapter()
