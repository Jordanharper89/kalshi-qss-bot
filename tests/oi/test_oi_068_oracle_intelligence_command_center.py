from qseries_v2.oracle_intelligence.oracle_intelligence_command_center import OracleIntelligenceCommandCenter


class FakeRuntime:
    def __init__(self):
        self.running = False
        self.outputs = {}
        self.cycles = 0

    def start(self):
        self.running = True
        return self.status()

    def stop(self):
        self.running = False
        return self.status()

    def status(self):
        return {
            "module": "fake_runtime",
            "status": "running" if self.running else "stopped",
            "read_only": True,
            "uptime_seconds": 1.0,
            "cycles": self.cycles,
            "last_cycle_at": "now",
            "metrics": {
                "markets_scanned": 1,
                "opportunities_found": 1,
                "queued_added": 1,
                "research_runs": 1,
                "refreshes": 0,
                "drift_checks": 1,
                "notifications": 0,
                "portfolio_updates": 1,
                "errors": 0,
            },
            "queue": {"status": "ok", "queued": 1, "processed": 0},
            "scheduler": {"status": "ok", "scheduled_jobs": 0},
            "refresh": {"status": "ok", "active_sessions": 1},
            "health": "healthy",
        }

    def run_once(self, markets=None, **kwargs):
        self.running = True
        self.cycles += 1
        self.outputs = {
            "status": "ok",
            "cycle": self.cycles,
            "started_at": "start",
            "completed_at": "end",
            "discovery": {"markets_scanned": len(markets or []), "opportunities_found": 1},
            "research": {"tracked_sessions": 1},
            "refresh": {"refreshed_count": 0},
            "notifications": {"notification_count": 0},
            "portfolio": {"portfolio_state": {"state": "normal"}},
        }
        return self.outputs

    def last_outputs(self):
        return self.outputs


def test_oi_068_oracle_intelligence_command_center():
    center = OracleIntelligenceCommandCenter(FakeRuntime())

    start = center.start_runtime()
    assert start["status"] == "ok"
    assert start["runtime"]["status"] == "running"

    run = center.run_once(markets=[{"ticker": "CMD-TEST"}])
    assert run["status"] == "ok"
    assert run["dashboard"]["last_cycle"]["opportunities_found"] == 1

    dash = center.dashboard()
    assert dash["status"] == "ok"
    assert dash["read_only"] is True
    assert dash["runtime"]["health"] == "healthy"

    health = center.health_report()
    assert health["health"] == "healthy"
    assert health["warnings"] == []

    text = center.command_summary_text()
    assert "ORACLE INTELLIGENCE COMMAND CENTER" in text
    assert "Oracle is read-only research" in text

    stop = center.stop_runtime()
    assert stop["runtime"]["status"] == "stopped"

    status = center.status()
    assert status["status"] == "ok"

    print("[PASS] OI-068 Oracle Intelligence Command Center")
    print({
        "runtime_status": status["runtime_status"],
        "health": status["health"],
        "cycles": status["cycles"],
    })


if __name__ == "__main__":
    test_oi_068_oracle_intelligence_command_center()
