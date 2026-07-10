
from qseries_v2.oracle_intelligence.macro_event_discovery_model.macro_event_discovery_contract import (
    MacroEventDiscoveryFamily,
    MacroEventDiscoveryRequest,
)
from qseries_v2.oracle_intelligence.macro_event_discovery_model.macro_event_discovery_engine import MacroEventDiscoveryEngine


def test_med_003_macro_event_discovery_engine():
    raw = [
        {
            "event_id": "fomc_2026_01",
            "title": "FOMC Rate Decision",
            "family": "fed_event",
            "region": "us",
            "country": "us",
            "currency": "usd",
            "impact": "high",
            "scheduled_at": "2026-01-28T19:00:00Z",
            "forecast": "4.50%",
            "previous": "4.50%",
            "affected_markets": ["RATES", "PREDICTION_MARKETS"],
        },
        {
            "id": "cpi_2026_01",
            "event": "US CPI YoY",
            "category": "inflation_event",
            "area": "us",
            "ccy": "usd",
            "importance": "high",
            "time": "2026-01-15T13:30:00Z",
            "consensus": "2.9%",
            "previous": "3.0%",
            "markets": "RATES, EQUITIES, PREDICTION_MARKETS",
        },
        {
            "event_id": "minor_2026_01",
            "title": "Minor Survey",
            "family": "economic_release",
            "region": "us",
            "currency": "usd",
            "impact": "low",
            "scheduled_at": "2026-01-12T14:00:00Z",
            "affected_markets": ["LOCAL"],
        },
    ]

    request = MacroEventDiscoveryRequest(
        request_id="med003.test.request",
        family=MacroEventDiscoveryFamily.ECONOMIC_RELEASE,
        source_name="med_003_test_feed",
        metadata={"raw_records": raw},
    )

    engine = MacroEventDiscoveryEngine(min_event_score=0.55)
    caps = engine.capabilities()
    health = engine.health()
    report_a = engine.discover(request)
    report_b = engine.discover(request)

    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.metadata["execution"] is False
    assert health.status == "ok"
    assert health.read_only is True

    assert report_a.schema_version == "MED-001"
    assert report_a.engine_id == "oracle.discovery.macro_event"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.opportunities) == 2

    assert [o.opportunity_id for o in report_a.opportunities] == [o.opportunity_id for o in report_b.opportunities]

    first = report_a.opportunities[0]
    assert first.read_only is True
    assert first.opportunity_type == "macro_event_signal"
    assert first.source_engine_id == "oracle.discovery.macro_event"
    assert first.event_score >= 0.55
    assert 0.0 <= first.confidence <= 1.0
    assert first.universal_market["market_type"] == "macro_event"
    assert first.universal_market["read_only"] is True
    assert first.universal_market["execution_allowed"] is False
    assert first.universal_market["order_allowed"] is False
    assert first.universal_market["position_sizing_allowed"] is False

    try:
        first.universal_market["execution_allowed"] = True
        raise AssertionError("universal_market should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["telemetry"]["records_seen"] == 3
    assert d["telemetry"]["events_seen"] == 3
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["rejected_records"] == 1
    assert d["telemetry"]["read_only"] is True

    print("[PASS] MED-003 Macro Event Discovery Engine")
    print({
        "schema_version": "MED-003",
        "engine_id": d["engine_id"],
        "status": d["status"],
        "opportunities": len(d["opportunities"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_med_003_macro_event_discovery_engine()
