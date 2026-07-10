
from qseries_v2.oracle_intelligence.news_intelligence_discovery_model.news_intelligence_discovery_replay_ledger import (
    NewsIntelligenceDiscoveryReplayLedger,
)


def test_nid_008_news_intelligence_discovery_replay_ledger():
    raw = [
        {"article_id": "article_b", "headline": "Fed signals slower cuts after inflation surprise", "publisher": "MarketWire", "link": "https://example.test/fed", "time": "2026-01-15T14:00:00Z", "category": "fed", "sentiment": "hawkish", "importance": "high", "relevance": 0.91, "markets": "RATES, EQUITIES, PREDICTION_MARKETS", "symbols": "FED, CPI"},
        {"id": "article_a", "title": "CPI comes in hotter than expected", "source": "EconomicDesk", "url": "https://example.test/cpi", "published_at": "2026-01-15T13:30:00Z", "topic": "inflation", "sentiment": "negative", "impact": "high", "relevance_score": 0.95, "affected_markets": ["RATES", "PREDICTION_MARKETS"], "entities": ["CPI", "USD"]},
        {"article_id": "article_minor", "title": "Local market commentary", "source": "SmallWire", "published_at": "2026-01-15T12:00:00Z", "topic": "local", "impact": "low", "relevance_score": 0.20, "affected_markets": ["LOCAL"]},
    ]

    ledger = NewsIntelligenceDiscoveryReplayLedger()
    caps = ledger.capabilities()
    health = ledger.health()

    baseline = ledger.run_discovery_and_record(raw, source_name="nid_008_test_source", min_news_score=0.55)
    replay = ledger.run_discovery_and_record(list(reversed(raw)), source_name="nid_008_test_source", min_news_score=0.55)
    comparison = ledger.compare(baseline, replay)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert caps["deterministic"] is True
    assert caps["canonicalizes_volatile_fields"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert baseline.schema_version == "NID-008"
    assert baseline.ledger_id == "oracle.discovery.ledger.news_intelligence_replay"
    assert baseline.status == "passed"
    assert baseline.read_only is True
    assert len(baseline.entries) == 2

    assert baseline.run_fingerprint == replay.run_fingerprint
    assert comparison.matching is True
    assert comparison.status == "matched"

    first = baseline.entries[0]
    assert first.read_only is True
    assert first.replay_status == "recorded"
    assert first.packet_fingerprint
    assert first.payload_fingerprint
    assert first.audit_fingerprint
    assert first.payload_summary["validation_required"] is True
    assert first.payload_summary["ranking_required"] is True
    assert first.payload_summary["registry_required"] is True
    assert first.payload_summary["execution_allowed"] is False
    assert first.payload_summary["order_allowed"] is False
    assert first.payload_summary["position_sizing_allowed"] is False
    assert first.payload_summary["read_only"] is True

    try:
        first.payload_summary["execution_allowed"] = True
        raise AssertionError("payload summary should be immutable")
    except TypeError:
        pass

    d = baseline.to_dict()
    c = comparison.to_dict()
    assert d["telemetry"]["packets_seen"] == 2
    assert d["telemetry"]["entries_emitted"] == 2
    assert "created_at" in d["telemetry"]["volatile_fields_excluded"]
    assert c["matching"] is True
    assert c["baseline_entries"] == 2
    assert c["replay_entries"] == 2

    print("[PASS] NID-008 News Intelligence Discovery Replay Ledger")
    print({
        "schema_version": d["schema_version"],
        "ledger_id": d["ledger_id"],
        "status": d["status"],
        "entries": len(d["entries"]),
        "replay_match": c["matching"],
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_nid_008_news_intelligence_discovery_replay_ledger()
