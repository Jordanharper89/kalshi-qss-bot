from qseries_v2.oracle_intelligence.autonomous_research_runtime import AutonomousResearchRuntime


class FakeDiscovery:
    def discover(self, markets, min_score=55, limit=100):
        return {
            "status": "ok",
            "read_only": True,
            "markets_scanned": len(markets),
            "opportunities_found": 1,
            "top_opportunities": [
                {
                    "ticker": "AUTO-TEST",
                    "opportunity_score": 91,
                    "priority": "critical",
                    "priority_weight": 5,
                    "market": {"ticker": "AUTO-TEST", "price": 52},
                }
            ],
        }


class FakeQueue:
    def __init__(self):
        self.count = 0

    def status(self):
        return {"status": "ok", "queued": self.count, "processed": 0}

    def ingest_discovery_result(self, discovery):
        self.count += len(discovery.get("top_opportunities", []))
        return {"status": "ok", "read_only": True, "added": 1, "updated": 0, "skipped": 0, "queued": self.count}


class FakeScheduler:
    def status(self):
        return {"status": "ok", "scheduled_jobs": 0}


class FakeLifecycle:
    def __init__(self):
        self.sessions = []

    def run_batch_and_track(self, min_score=55, max_jobs=3, report_format="terminal"):
        self.sessions.append({
            "ticker": "AUTO-TEST",
            "status": "ACTIVE",
            "opportunity": {"opportunity_score": 91, "priority": "critical"},
            "current_snapshot": {
                "consensus_side": "YES",
                "consensus_score_pct": 88,
                "adjusted_confidence": 84,
                "final_research_grade": "A",
                "research_stability": "high",
                "risk_level": "low",
                "tail_risk_level": "low",
            },
            "drift": {"drift_level": "none"},
        })
        return {"status": "ok", "read_only": True, "tracked_sessions": 1, "completed_count": 1, "error_count": 0}

    def portfolio_snapshot(self):
        return {"status": "ok", "read_only": True, "active_count": len(self.sessions), "sessions": self.sessions}


class FakeRefresh:
    def status(self):
        return {"status": "ok", "active_sessions": 1, "refresh_history": 0}

    def refresh_due_sessions(self, max_refreshes=3, report_format="terminal"):
        return {"status": "ok", "read_only": True, "refreshed_count": 0, "error_count": 0}


class FakeDrift:
    def detect_portfolio_drift(self, portfolio):
        return {
            "status": "ok",
            "read_only": True,
            "sessions_analyzed": len(portfolio.get("sessions", [])),
            "top_drifts": [],
        }


class FakeNotify:
    def build_portfolio_notifications(self, drift_result, channel="telegram", force=False):
        return {"status": "ok", "read_only": True, "notification_count": 0, "notifications": []}


class FakePortfolio:
    def analyze_portfolio(self, portfolio):
        return {
            "status": "ok",
            "read_only": True,
            "active_count": portfolio.get("active_count", 0),
            "portfolio_state": {"state": "normal"},
        }


def test_oi_067_autonomous_research_runtime():
    runtime = AutonomousResearchRuntime(
        discovery_engine=FakeDiscovery(),
        queue_manager=FakeQueue(),
        scheduler=FakeScheduler(),
        lifecycle_bridge=FakeLifecycle(),
        refresh_engine=FakeRefresh(),
        drift_engine=FakeDrift(),
        notification_engine=FakeNotify(),
        portfolio_manager=FakePortfolio(),
    )

    started = runtime.start()
    assert started["status"] == "running"
    assert started["read_only"] is True

    result = runtime.run_cycle(
        markets=[{"ticker": "AUTO-TEST", "price": 52}],
        max_research_jobs=1,
    )

    assert result["status"] == "ok"
    assert result["discovery"]["opportunities_found"] == 1
    assert result["research"]["tracked_sessions"] == 1
    assert result["portfolio"]["active_count"] == 1

    status = runtime.status()
    assert status["status"] == "running"
    assert status["metrics"]["markets_scanned"] == 1
    assert status["metrics"]["research_runs"] == 1
    assert status["health"] == "healthy"

    stopped = runtime.stop()
    assert stopped["status"] == "stopped"

    print("[PASS] OI-067 Autonomous Research Runtime")
    print(status)


if __name__ == "__main__":
    test_oi_067_autonomous_research_runtime()
