
from qseries_v2.oracle_intelligence.universal_market_adapter_discovery_engine import (
    ENGINE_ID,
    Q_SERIES_EXECUTION_OWNER,
    AdapterDiscoverySource,
    UniversalMarketAdapterDiscoveryEngine,
    architecture_contract,
    demo_sources,
    discover_adapters,
    snapshot_to_json,
)


def test_discovery_snapshot_core_contract():
    snapshot = discover_adapters(demo_sources(), discovered_at=1760000000.0)

    assert snapshot.engine_id == ENGINE_ID
    assert snapshot.result_count == 2
    assert snapshot.replay_hash
    assert snapshot.architecture["oracle_mode"] == "read_only"
    assert snapshot.architecture["execution_owner"] == Q_SERIES_EXECUTION_OWNER

    classifications = {result.source.source_id: result.classification for result in snapshot.results}
    assert classifications["demo.kalshi.prediction_markets"] in {"adapter_ready", "adapter_candidate"}
    assert classifications["demo.crypto.partial"] in {"research_required", "not_ready", "adapter_candidate"}


def test_read_only_guardrails_and_explainability():
    source = AdapterDiscoverySource(
        source_id="test.weather.discovery",
        name="Weather Discovery Fixture",
        market_type="weather",
        source_kind="registry_item",
        schema_fields=(
            "event_id",
            "market_id",
            "market_type",
            "title",
            "status",
            "timestamp",
            "settlement_source",
            "source_url",
        ),
        sample_payload={
            "event_id": "WX-001",
            "market_id": "WX-MKT-001",
            "market_type": "weather",
            "title": "Temperature threshold fixture",
            "status": "observed",
            "timestamp": "2026-07-02T00:00:00Z",
            "settlement_source": "official_weather_station",
            "source_url": "read_only://weather/source",
        },
        rate_limit="documented",
        terms_status="approved_for_read_only_research",
        historical_available=True,
        health_probe="fixture_validation",
    )

    snapshot = discover_adapters([source], discovered_at=1760000000.0)
    result = snapshot.results[0]

    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == Q_SERIES_EXECUTION_OWNER
    assert "cannot execute" in result.explanation["read_only_statement"]
    assert result.replay_key
    assert result.readiness_score > 0.60


def test_engine_history_and_json_serialization():
    engine = UniversalMarketAdapterDiscoveryEngine()
    snapshot = engine.discover(demo_sources(), market_scope=["prediction_markets"], discovered_at=1760000000.0)

    assert engine.latest_snapshot() == snapshot
    assert len(engine.history()) == 1
    assert snapshot.result_count == 1

    text = snapshot_to_json(snapshot)
    assert "Oracle Universal Market Adapter Discovery Engine" in text
    assert "read_only" in text


def test_architecture_contract_is_institutional():
    contract = architecture_contract()

    assert contract["oracle_mode"] == "read_only"
    assert contract["universal_market_model"] is True
    assert contract["adapter_based_expansion"] is True
    assert contract["explainability_by_default"] is True
    assert contract["replayability_by_default"] is True
    assert contract["institutional_telemetry"] is True
    assert contract["strategy_agnostic_q_series"] is True
    assert contract["execution_owner"] == Q_SERIES_EXECUTION_OWNER


if __name__ == "__main__":
    test_discovery_snapshot_core_contract()
    test_read_only_guardrails_and_explainability()
    test_engine_history_and_json_serialization()
    test_architecture_contract_is_institutional()
    print("[PASS] OI-176 Universal Market Adapter Discovery Engine")
    print(discover_adapters(demo_sources(), discovered_at=1760000000.0).to_dict())
