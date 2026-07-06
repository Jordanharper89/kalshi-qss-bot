from qseries_v2.oracle_intelligence.oracle_intelligence_runtime_orchestrator import OracleIntelligenceRuntimeOrchestrator


class FakeLearningLoop:
    def __init__(self):
        self.events = 0

    def diagnostics(self):
        return {
            "module": "fake_learning_loop",
            "status": "ok",
            "events_processed": self.events,
            "read_only": True,
            "execution_allowed": False,
        }

    def process_market_snapshot(self, snapshot):
        self.events += 1
        return {
            "status": "ok",
            "event_type": "market_snapshot",
            "snapshot_count": 1,
            "historical_update": {"status": "ok", "recorded": True},
            "relationship_update": {"status": "ok", "monitor_summary": {"total_alerts": 1}},
            "forecast_update": {
                "status": "ok",
                "reports_generated": 1,
                "reports": [{"ticker": snapshot.get("ticker"), "summary": {"forecast_direction": "yes_up_bias"}}],
            },
            "explanation_update": {
                "status": "ok",
                "explanations_generated": 1,
                "explanations": [{"headline": f"{snapshot.get('ticker')} explanation"}],
            },
            "learning_summary": {
                "events_processed": self.events,
                "forecast_reports": 1,
                "explanations": 1,
            },
            "read_only": True,
            "execution_allowed": False,
        }

    def process_market_batch(self, snapshots):
        self.events += 1
        return {
            "status": "ok",
            "event_type": "market_snapshot_batch",
            "snapshot_count": len(snapshots),
            "historical_update": {"status": "ok", "recorded": True},
            "relationship_update": {"status": "ok", "monitor_summary": {"total_alerts": 2}},
            "forecast_update": {
                "status": "ok",
                "reports_generated": len(snapshots),
                "reports": [{"ticker": s.get("ticker")} for s in snapshots],
            },
            "explanation_update": {
                "status": "ok",
                "explanations_generated": len(snapshots),
                "explanations": [{"headline": f"{s.get('ticker')} explanation"} for s in snapshots],
            },
            "learning_summary": {
                "events_processed": self.events,
                "forecast_reports": len(snapshots),
                "explanations": len(snapshots),
            },
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_040_oracle_intelligence_runtime_orchestrator():
    runtime = OracleIntelligenceRuntimeOrchestrator(learning_loop=FakeLearningLoop())

    diagnostics = runtime.diagnostics()
    assert diagnostics["runtime_status"] == "stopped"
    assert diagnostics["learning_loop_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    start = runtime.start()
    assert start["runtime_status"] == "running"

    packet = runtime.process_snapshot({
        "ticker": "BTC",
        "category": "crypto",
        "yes_price": 62,
    })

    assert packet["status"] == "ok"
    assert packet["runtime_status"] == "running"
    assert packet["snapshots_processed"] == 1
    assert packet["batches_processed"] == 0
    assert packet["last_event"]["snapshot_count"] == 1
    assert packet["intelligence_packet"]["forecast_update"]["reports_generated"] == 1
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    batch = runtime.process_batch([
        {"ticker": "ETH", "category": "crypto", "yes_price": 55},
        {"ticker": "GOLD", "category": "macro", "yes_price": 45},
    ])

    assert batch["snapshots_processed"] == 3
    assert batch["batches_processed"] == 1
    assert batch["last_event"]["snapshot_count"] == 2
    assert batch["intelligence_packet"]["forecast_update"]["reports_generated"] == 2

    payload = runtime.api_payload()
    assert payload["runtime_status"] == "running"
    assert payload["snapshots_processed"] == 3
    assert payload["read_only"] is True
    assert payload["execution_allowed"] is False

    stop = runtime.stop()
    assert stop["runtime_status"] == "stopped"

    print("[PASS] OI-040 Oracle Intelligence Runtime Orchestrator")
    print({
        "snapshots_processed": batch["snapshots_processed"],
        "batches_processed": batch["batches_processed"],
        "runtime_status": payload["runtime_status"],
    })


if __name__ == "__main__":
    test_oi_040_oracle_intelligence_runtime_orchestrator()
