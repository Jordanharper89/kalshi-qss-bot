
from qseries_v2.oracle_intelligence.macro_event_discovery_model.macro_event_source_adapter import MacroEventSourceAdapter


def test_med_002_macro_event_source_adapter():
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
    ]

    adapter = MacroEventSourceAdapter(source_name="med_002_test_feed")
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

    assert batch_a.schema_version == "MED-002"
    assert batch_a.adapter_id == "oracle.discovery.source.macro_event"
    assert batch_a.read_only is True
    assert len(batch_a.snapshots) == 2

    order_a = [s.event_id for s in batch_a.snapshots]
    order_b = [s.event_id for s in batch_b.snapshots]
    assert order_a == order_b
    assert order_a == ["cpi_2026_01", "fomc_2026_01"]

    first = batch_a.snapshots[0]
    assert first.title == "US CPI YoY"
    assert first.family == "inflation_event"
    assert first.region == "US"
    assert first.country == "US"
    assert first.currency == "USD"
    assert first.impact == "high"
    assert first.forecast == "2.9%"
    assert first.previous == "3.0%"
    assert first.affected_markets == ("RATES", "EQUITIES", "PREDICTION_MARKETS")
    assert first.read_only is True

    try:
        first.metadata["x"] = "mutation"
        raise AssertionError("metadata should be immutable")
    except TypeError:
        pass

    d = batch_a.to_dict()
    assert d["schema_version"] == "MED-002"
    assert d["telemetry"]["raw_records_seen"] == 2
    assert d["telemetry"]["snapshots_emitted"] == 2
    assert d["telemetry"]["events_seen"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] MED-002 Macro Event Source Adapter")
    print({
        "schema_version": d["schema_version"],
        "adapter_id": d["adapter_id"],
        "snapshots": len(d["snapshots"]),
        "events_seen": d["telemetry"]["events_seen"],
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_med_002_macro_event_source_adapter()
