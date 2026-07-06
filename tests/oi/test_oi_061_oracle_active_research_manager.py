from qseries_v2.oracle_intelligence.oracle_active_research_manager import OracleActiveResearchManager


def fake_result(ticker, side="YES", consensus=88, confidence=84, grade="A-", stability="high"):
    return {
        "ticker": ticker,
        "report": {
            "packet": {
                "summary": {
                    "market_ticker": ticker,
                    "expected_resolution": side,
                    "expected_probability": 0.82,
                    "adjusted_confidence": confidence,
                    "risk_level": "low",
                    "tail_risk_level": "low",
                    "analog_count": 12,
                },
                "signals": {
                    "final_research_grade": grade,
                    "adjusted_confidence": confidence,
                },
                "consensus": {
                    "consensus_side": side,
                    "consensus_score_pct": consensus,
                    "agreement_pct": 92,
                    "research_stability": stability,
                    "research_certainty_index": 90,
                },
            }
        },
    }


def test_oi_061_oracle_active_research_manager():
    manager = OracleActiveResearchManager()

    started = manager.start_session(
        ticker="ACTIVE-TEST",
        opportunity={"opportunity_score": 91.0},
        research_result=fake_result("ACTIVE-TEST", consensus=88, confidence=84),
    )

    assert started["ticker"] == "ACTIVE-TEST"
    assert started["status"] == "ACTIVE"
    assert started["refresh_count"] == 0
    assert started["current_snapshot"]["consensus_score_pct"] == 88.0

    refreshed = manager.refresh_session(
        ticker="ACTIVE-TEST",
        research_result=fake_result("ACTIVE-TEST", consensus=94, confidence=91, grade="A"),
    )

    assert refreshed["refresh_count"] == 1
    assert refreshed["drift"]["consensus_score_drift"] == 6.0
    assert refreshed["drift"]["confidence_drift"] == 7.0
    assert refreshed["drift"]["grade_changed"] is True
    assert refreshed["drift"]["drift_level"] in {"minor", "moderate", "major"}

    sessions = manager.active_sessions()
    assert len(sessions) == 1

    portfolio = manager.portfolio_snapshot()
    assert portfolio["active_count"] == 1
    assert portfolio["drift_counts"]["meaningful_confidence_drift"] == 1

    completed = manager.complete_session("ACTIVE-TEST")
    assert completed["status"] == "COMPLETED"

    archived = manager.archive_session("ACTIVE-TEST")
    assert archived["status"] == "ok"
    assert archived["active_sessions"] == 0
    assert archived["archived_sessions"] == 1

    fetched = manager.get_session("ACTIVE-TEST")
    assert fetched["status"] == "ARCHIVED"

    status = manager.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True
    assert status["active_sessions"] == 0
    assert status["archived_sessions"] == 1

    print("[PASS] OI-061 Oracle Active Research Manager")
    print(status)


if __name__ == "__main__":
    test_oi_061_oracle_active_research_manager()
