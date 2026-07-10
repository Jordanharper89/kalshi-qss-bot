
from qseries_v2.oracle_intelligence.social_intelligence_discovery_model.social_intelligence_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    SocialIntelligenceFamily,
    SocialIntelligenceDiscoveryRequest,
    EmptySocialIntelligenceDiscoveryEngine,
)


def test_sid_001_social_intelligence_discovery_contract():
    request = SocialIntelligenceDiscoveryRequest(
        request_id="social.intelligence.discovery.test.request",
        family=SocialIntelligenceFamily.SOCIAL_MOMENTUM,
        source_name="test_source",
        post_ids=("post_a", "post_b"),
        topics=("Kalshi", "inflation"),
        markets=("prediction_markets", "rates"),
        metadata={"records": [{"post_id": "post_a", "topic": "kalshi"}]},
    )

    engine = EmptySocialIntelligenceDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "SID-001"
    assert CONTRACT_ID == "oracle.discovery.contract.social_intelligence"

    assert request.read_only is True
    assert request.post_ids == ("post_a", "post_b")
    assert request.topics == ("kalshi", "inflation")
    assert request.markets == ("PREDICTION_MARKETS", "RATES")
    assert request.family == SocialIntelligenceFamily.SOCIAL_MOMENTUM

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

    assert result.schema_version == "SID-001"
    assert result.engine_id == "oracle.discovery.social_intelligence.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.posts_seen == 0
    assert result.telemetry.opportunities_emitted == 0

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "SID-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] SID-001 Social Intelligence Discovery Contract")
    print({
        "schema_version": d["schema_version"],
        "engine_id": d["engine_id"],
        "status": d["status"],
        "opportunities": len(d["opportunities"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_sid_001_social_intelligence_discovery_contract()
