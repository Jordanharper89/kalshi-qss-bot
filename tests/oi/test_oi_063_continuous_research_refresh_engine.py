from datetime import datetime, timezone, timedelta

from qseries_v2.oracle_intelligence.oracle_active_research_manager import OracleActiveResearchManager
from qseries_v2.oracle_intelligence.active_research_lifecycle_bridge import ActiveResearchLifecycleBridge
from qseries_v2.oracle_intelligence.continuous_research_refresh_engine import ContinuousResearchRefreshEngine


class FakeExecutionBridge:
    def status(self):
        return {"status": "ok"}


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


def test_oi_063_continuous_research_refresh_engine():
    manager = OracleActiveResearchManager()
    lifecycle = ActiveResearchLifecycleBridge(FakeExecutionBridge(), manager)
    refresh = ContinuousResearchRefreshEngine(lifecycle)

    lifecycle.track_external_result(
        fake_result("REFRESH-TEST", consensus=88, confidence=84),
        opportunity={
            "ticker": "REFRESH-TEST",
            "opportunity_score": 91,
            "priority": "critical",
        },
    )

    session = manager.get_session("REFRESH-TEST")
    old_time = (datetime.now(timezone.utc) - timedelta(seconds=20)).isoformat()
    manager._sessions["REFRESH-TEST"]["last_updated"] = old_time

    due = refresh.evaluate_refresh_due()
    assert due["status"] == "ok"
    assert due["due_count"] == 1
    assert due["due"][0]["ticker"] == "REFRESH-TEST"

    result = refresh.refresh_due_sessions(max_refreshes=1)
    assert result["status"] == "ok"
    assert result["refreshed_count"] == 1
    assert result["refreshed"][0]["ticker"] == "REFRESH-TEST"

    refreshed_session = manager.get_session("REFRESH-TEST")
    assert refreshed_session["refresh_count"] == 1
    assert refreshed_session["drift"]["consensus_score_drift"] > 0

    forced = refresh.force_refresh("REFRESH-TEST")
    assert forced["status"] == "ok"
    assert forced["ticker"] == "REFRESH-TEST"

    history = refresh.refresh_history()
    assert history["count"] == 2

    status = refresh.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-063 Continuous Research Refresh Engine")
    print({
        "refresh_history": status["refresh_history"],
        "active_sessions": status["active_sessions"],
        "latest_drift": manager.get_session("REFRESH-TEST")["drift"],
    })


if __name__ == "__main__":
    test_oi_063_continuous_research_refresh_engine()
