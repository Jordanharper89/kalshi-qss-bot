from qseries_v2.oracle_intelligence.event_driven_learning_loop import EventDrivenLearningLoop


class FakeHistoryPipeline:
    def record_batch(self, snapshots):
        return {"status": "ok", "records": len(snapshots)}


class FakeRelationshipMonitor:
    def monitor(self, snapshots):
        return {
            "status": "ok",
            "live_markets_analyzed": len(snapshots),
            "monitor_summary": {"total_alerts": 1},
            "read_only": True,
            "execution_allowed": False,
        }


class FakeForecastService:
    def api_payload(self, snapshot):
        return {
            "status": "ok",
            "ticker": snapshot.get("ticker"),
            "summary": {"forecast_direction": "yes_up_bias"},
            "read_only": True,
            "execution_allowed": False,
        }


class FakeExplanationEngine:
    def api_payload(self, snapshot):
        return {
            "status": "ok",
            "headline": f"{snapshot.get('ticker')} explanation",
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_039_event_driven_learning_loop():
    loop = EventDrivenLearningLoop(
        history_pipeline=FakeHistoryPipeline(),
        relationship_monitor=FakeRelationshipMonitor(),
        forecast_service=FakeForecastService(),
        explanation_engine=FakeExplanationEngine(),
    )

    diagnostics = loop.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["history_pipeline_ready"] is True
    assert diagnostics["relationship_monitor_ready"] is True
    assert diagnostics["forecast_service_ready"] is True
    assert diagnostics["explanation_engine_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    snapshots = [
        {"ticker": "BTC", "category": "crypto", "yes_price": 62, "price_change": 3.1},
        {"ticker": "ETH", "category": "crypto", "yes_price": 55, "price_change": 1.2},
    ]

    packet = loop.process_market_batch(snapshots)

    assert packet["status"] == "ok"
    assert packet["event_type"] == "market_snapshot_batch"
    assert packet["snapshot_count"] == 2
    assert packet["historical_update"]["recorded"] is True
    assert packet["relationship_update"]["status"] == "ok"
    assert packet["forecast_update"]["reports_generated"] == 2
    assert packet["explanation_update"]["explanations_generated"] == 2
    assert packet["learning_summary"]["events_processed"] == 1
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    single = loop.process_market_snapshot({"ticker": "GOLD", "category": "macro", "yes_price": 45})
    assert single["snapshot_count"] == 1

    latest = loop.latest()
    assert latest["status"] == "ok"

    print("[PASS] OI-039 Event-Driven Learning Loop")
    print({
        "event_type": packet["event_type"],
        "snapshot_count": packet["snapshot_count"],
        "summary": packet["learning_summary"],
    })


if __name__ == "__main__":
    test_oi_039_event_driven_learning_loop()
