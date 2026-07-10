
from qseries_v2.oracle_intelligence.social_intelligence_discovery_model.social_intelligence_discovery_registry_bridge import (
    SocialIntelligenceDiscoveryRegistryBridge,
)


def test_sid_005_social_intelligence_discovery_registry_bridge():
    raw = [
        {"post_id": "post_b", "platform": "X", "author": "macro_trader", "topic": "fed", "text": "Rate cut odds are collapsing after CPI reaction.", "posted_at": "2026-01-15T14:05:00Z", "sentiment": "bearish", "engagement_score": 0.88, "velocity_score": 0.82, "credibility_score": 0.80, "markets": "RATES, PREDICTION_MARKETS", "symbols": "FED, CPI"},
        {"id": "post_a", "network": "reddit", "username": "kalshi_watcher", "category": "prediction_market_social", "content": "Inflation markets are moving fast after the CPI headline.", "time": "2026-01-15T13:35:00Z", "sentiment": "bullish", "engagement": 0.91, "velocity": 0.87, "credibility": 0.76, "affected_markets": ["PREDICTION_MARKETS", "RATES"], "entities": ["CPI", "KALSHI"]},
        {"post_id": "post_minor", "platform": "x", "author": "small_account", "topic": "local", "text": "Random local market comment.", "posted_at": "2026-01-15T12:00:00Z", "sentiment": "neutral", "engagement_score": 0.10, "velocity_score": 0.10, "credibility_score": 0.20, "affected_markets": ["LOCAL"]},
    ]

    bridge = SocialIntelligenceDiscoveryRegistryBridge()
    caps = bridge.capabilities()
    health = bridge.health()
    report_a = bridge.discover_and_bridge(raw, source_name="sid_005_test_source", min_social_score=0.55)
    report_b = bridge.discover_and_bridge(list(reversed(raw)), source_name="sid_005_test_source", min_social_score=0.55)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert caps["posting_allowed"] is False
    assert caps["dm_allowed"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "SID-005"
    assert report_a.bridge_id == "oracle.discovery.bridge.social_intelligence_registry"
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
    assert first.payload["posting_allowed"] is False
    assert first.payload["dm_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["social_action_fields_present"] is False
    assert first.payload["universal_market"]["market_type"] == "social_intelligence"

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
    assert d["telemetry"]["posting_allowed"] is False

    print("[PASS] SID-005 Social Intelligence Discovery Registry Bridge")
    print({
        "schema_version": d["schema_version"],
        "bridge_id": d["bridge_id"],
        "status": d["status"],
        "records": len(d["records"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_sid_005_social_intelligence_discovery_registry_bridge()
