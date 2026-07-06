from qseries_v2.oracle_intelligence.active_research_lifecycle_bridge import ActiveResearchLifecycleBridge
from qseries_v2.oracle_intelligence.oracle_active_research_manager import OracleActiveResearchManager


class FakeExecutionBridge:
    def __init__(self):
        self.calls = 0

    def status(self):
        return {"status": "ok"}

    def run_next_research(self, min_score=55.0, report_format="terminal"):
        self.calls += 1
        return fake_result("LIFE-TEST", consensus=88 + self.calls, confidence=84 + self.calls)

    def run_batch(self, min_score=55.0, max_jobs=3, report_format="terminal"):
        return {
            "status": "ok",
            "read_only": True,
            "completed_count": 2,
            "error_count": 0,
            "results": [
                fake_result("LIFE-BATCH-1", consensus=86, confidence=82),
                fake_result("LIFE-BATCH-2", consensus=90, confidence=87),
            ],
        }


def fake_result(ticker, consensus=88, confidence=84):
    return {
        "status": "ok",
        "read_only": True,
        "research_only_execution": True,
        "ticker": ticker,
        "job": {
            "ticker": ticker,
            "opportunity": {
                "ticker": ticker,
                "opportunity_score": 91,
                "priority": "critical",
            },
        },
        "report": {
            "packet": {
                "summary": {
                    "market_ticker": ticker,
                    "expected_resolution": "YES",
                    "expected_probability": 0.82,
                    "adjusted_confidence": confidence,
                    "risk_level": "low",
                    "tail_risk_level": "low",
                    "analog_count": 12,
                },
                "signals": {
                    "final_research_grade": "A",
                    "adjusted_confidence": confidence,
                },
                "consensus": {
                    "consensus_side": "YES",
                    "consensus_score_pct": consensus,
                    "agreement_pct": 92,
                    "research_stability": "high",
                    "research_certainty_index": 90,
                },
            }
        },
    }


def test_oi_062_active_research_lifecycle_bridge():
    execution = FakeExecutionBridge()
    manager = OracleActiveResearchManager()
    bridge = ActiveResearchLifecycleBridge(execution, manager)

    first = bridge.run_next_and_track(min_score=80)
    assert first["status"] == "ok"
    assert first["session"]["ticker"] == "LIFE-TEST"
    assert first["session"]["refresh_count"] == 0

    second = bridge.run_next_and_track(min_score=80)
    assert second["status"] == "ok"
    assert second["session"]["ticker"] == "LIFE-TEST"
    assert second["session"]["refresh_count"] == 1
    assert second["session"]["drift"]["consensus_score_drift"] == 1.0

    batch = bridge.run_batch_and_track(min_score=70, max_jobs=2)
    assert batch["status"] == "ok"
    assert batch["tracked_sessions"] == 2

    portfolio = bridge.portfolio_snapshot()
    assert portfolio["active_count"] == 3

    closed = bridge.complete_and_archive("LIFE-TEST")
    assert closed["status"] == "ok"
    assert closed["archived"]["status"] == "ok"

    status = bridge.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-062 Active Research Lifecycle Bridge")
    print({
        "active_sessions": status["active_sessions"],
        "portfolio_active": bridge.portfolio_snapshot()["active_count"],
    })


if __name__ == "__main__":
    test_oi_062_active_research_lifecycle_bridge()
