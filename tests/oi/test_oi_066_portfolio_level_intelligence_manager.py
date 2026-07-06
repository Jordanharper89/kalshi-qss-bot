from qseries_v2.oracle_intelligence.portfolio_level_intelligence_manager import portfolio_level_intelligence_manager


def session(ticker, side="YES", consensus=90, confidence=86, grade="A", stability="high", risk="low", tail="low", drift_level="none", opp=90):
    return {
        "ticker": ticker,
        "status": "ACTIVE",
        "opportunity": {"priority": "critical", "opportunity_score": opp},
        "current_snapshot": {
            "consensus_side": side,
            "consensus_score_pct": consensus,
            "adjusted_confidence": confidence,
            "final_research_grade": grade,
            "research_stability": stability,
            "risk_level": risk,
            "tail_risk_level": tail,
        },
        "drift": {
            "drift_level": drift_level,
            "consensus_score_drift": 2,
            "confidence_drift": 3,
            "consensus_side_changed": False,
            "grade_changed": False,
            "stability_changed": False,
        },
    }


def test_oi_066_portfolio_level_intelligence_manager():
    portfolio = {
        "sessions": [
            session("PORT-1", side="YES", consensus=92, confidence=88),
            session("PORT-2", side="YES", consensus=89, confidence=85),
            session("PORT-3", side="NO", consensus=72, confidence=70, grade="B+", stability="medium", risk="medium", opp=75),
        ]
    }

    result = portfolio_level_intelligence_manager.analyze_portfolio(portfolio)

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["active_count"] == 3
    assert result["consensus_summary"]["yes_count"] == 2
    assert result["consensus_summary"]["no_count"] == 1
    assert result["top_research_priorities"][0]["ticker"] in {"PORT-1", "PORT-2"}
    assert "by_grade" in result["clusters"]

    status = portfolio_level_intelligence_manager.status()
    assert status["status"] == "ok"

    print("[PASS] OI-066 Portfolio-Level Intelligence Manager")
    print({
        "portfolio_state": result["portfolio_state"],
        "consensus": result["consensus_summary"],
        "top": result["top_research_priorities"][0],
    })


if __name__ == "__main__":
    test_oi_066_portfolio_level_intelligence_manager()
