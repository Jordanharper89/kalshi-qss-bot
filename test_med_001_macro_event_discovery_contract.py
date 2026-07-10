from qseries_v2.oracle_intelligence.macro_event_discovery_model.macro_event_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    MacroEventDiscoveryFamily,
    MacroEventDiscoveryRequest,
    EmptyMacroEventDiscoveryEngine,
)


def test_med_001_macro_event_discovery_contract():
    request = MacroEventDiscoveryRequest(
        request_id="macro.event.discovery.test.request",
        family=MacroEventDiscoveryFamily.ECONOMIC_RELEASE,
        source_name="test_source",
        event_ids=("cpi_2026_01", "fomc_2026_01"),
        regions=("us", "global"),
        markets=("rates", "prediction_markets"),
        metadata={"records": [{"event_id": "cpi_2026_01", "region": "US"}]},
    )

    engine = EmptyMacroEventDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "MED-001"
    assert CONTRACT_ID == "oracle.discovery.contract.macro_event"

    assert request.read_only is True
    assert request.event_ids == ("cpi_2026_01", "fomc_2026_01")
    assert request.regions == ("US", "GLOBAL")
    assert request.markets == ("RATES", "PREDICTION_MARKETS")
    assert request.family == MacroEventDiscoveryFamily.ECONOMIC_RELEASE

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

    assert result.schema_version == "MED-001"
    assert result.engine_id == "oracle.discovery.macro_event.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.events_seen == 0
    assert result.telemetry.opportunities_emitted == 0
    assert result.health.status == "ok"

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "MED-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] MED-001 Macro Event Discovery Contract")
    print(
        {
            "schema_version": d["schema_version"],
            "engine_id": d["engine_id"],
            "status": d["status"],
            "opportunities": len(d["opportunities"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_med_001_macro_event_discovery_contract()
