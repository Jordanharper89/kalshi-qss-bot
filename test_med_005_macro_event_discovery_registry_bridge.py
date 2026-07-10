
from qseries_v2.oracle_intelligence.macro_event_discovery_model.macro_event_discovery_registry_bridge import (
    MacroEventDiscoveryRegistryBridge,
)


def test_med_005_macro_event_discovery_registry_bridge():
    raw = [
        {"event_id": "fomc_2026_01", "title": "FOMC Rate Decision", "family": "fed_event", "region": "us", "currency": "usd", "impact": "high", "scheduled_at": "2026-01-28T19:00:00Z", "forecast": "4.50%", "previous": "4.50%", "affected_markets": ["RATES", "PREDICTION_MARKETS"]},
        {"id": "cpi_2026_01", "event": "US CPI YoY", "category": "inflation_event", "area": "us", "ccy": "usd", "importance": "high", "time": "2026-01-15T13:30:00Z", "consensus": "2.9%", "previous": "3.0%", "markets": "RATES, EQUITIES, PREDICTION_MARKETS"},
        {"event_id": "minor_2026_01", "title": "Minor Survey", "family": "economic_release", "region": "us", "currency": "usd", "impact": "low", "scheduled_at": "2026-01-12T14:00:00Z", "affected_markets": ["LOCAL"]},
    ]

    bridge = MacroEventDiscoveryRegistryBridge()
    caps = bridge.capabilities()
    health = bridge.health()
    report_a = bridge.discover_and_bridge(raw, source_name="med_005_test_source", min_event_score=0.55)
    report_b = bridge.discover_and_bridge(list(reversed(raw)), source_name="med_005_test_source", min_event_score=0.55)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "MED-005"
    assert report_a.bridge_id == "oracle.discovery.bridge.macro_event_registry"
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
    assert first.payload["universal_market"]["market_type"] == "macro_event"

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

    print("[PASS] MED-005 Macro Event Discovery Registry Bridge")
    print({
        "schema_version": d["schema_version"],
        "bridge_id": d["bridge_id"],
        "status": d["status"],
        "records": len(d["records"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_med_005_macro_event_discovery_registry_bridge()
