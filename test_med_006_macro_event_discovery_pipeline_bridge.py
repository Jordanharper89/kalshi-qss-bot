
from qseries_v2.oracle_intelligence.macro_event_discovery_model.macro_event_discovery_pipeline_bridge import (
    MacroEventDiscoveryPipelineBridge,
)


def test_med_006_macro_event_discovery_pipeline_bridge():
    raw = [
        {"event_id": "fomc_2026_01", "title": "FOMC Rate Decision", "family": "fed_event", "region": "us", "currency": "usd", "impact": "high", "scheduled_at": "2026-01-28T19:00:00Z", "forecast": "4.50%", "previous": "4.50%", "affected_markets": ["RATES", "PREDICTION_MARKETS"]},
        {"id": "cpi_2026_01", "event": "US CPI YoY", "category": "inflation_event", "area": "us", "ccy": "usd", "importance": "high", "time": "2026-01-15T13:30:00Z", "consensus": "2.9%", "previous": "3.0%", "markets": "RATES, EQUITIES, PREDICTION_MARKETS"},
        {"event_id": "minor_2026_01", "title": "Minor Survey", "family": "economic_release", "region": "us", "currency": "usd", "impact": "low", "scheduled_at": "2026-01-12T14:00:00Z", "affected_markets": ["LOCAL"]},
    ]

    bridge = MacroEventDiscoveryPipelineBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_registry_and_bridge(raw, source_name="med_006_test_source", min_event_score=0.55)
    report_b = bridge.discover_registry_and_bridge(list(reversed(raw)), source_name="med_006_test_source", min_event_score=0.55)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "MED-006"
    assert report_a.bridge_id == "oracle.discovery.bridge.macro_event_pipeline"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.packets) == 2

    assert [p.packet_id for p in report_a.packets] == [p.packet_id for p in report_b.packets]

    first = report_a.packets[0]
    assert first.read_only is True
    assert first.pipeline_status == "pipeline_ready"
    assert first.payload["read_only"] is True
    assert first.payload["validation_required"] is True
    assert first.payload["ranking_required"] is True
    assert first.payload["registry_required"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["order_allowed"] is False
    assert first.payload["position_sizing_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["handoff_target"] == "OOS Opportunity Pipeline"
    assert first.payload["registry_payload"]["universal_market"]["market_type"] == "macro_event"

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("pipeline payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "MED-006"
    assert d["telemetry"]["records_seen"] == 2
    assert d["telemetry"]["packets_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] MED-006 Macro Event Discovery Pipeline Bridge")
    print({
        "schema_version": d["schema_version"],
        "bridge_id": d["bridge_id"],
        "status": d["status"],
        "packets": len(d["packets"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_med_006_macro_event_discovery_pipeline_bridge()
