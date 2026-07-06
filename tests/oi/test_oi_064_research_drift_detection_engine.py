from qseries_v2.oracle_intelligence.research_drift_detection_engine import research_drift_detection_engine


def test_oi_064_research_drift_detection_engine():
    critical_session = {
        "ticker": "DRIFT-CRITICAL",
        "previous_snapshot": {
            "consensus_side": "YES",
            "consensus_score_pct": 88,
            "adjusted_confidence": 84,
            "research_stability": "high",
            "final_research_grade": "A",
        },
        "current_snapshot": {
            "consensus_side": "NO",
            "consensus_score_pct": 72,
            "adjusted_confidence": 70,
            "research_stability": "low",
            "final_research_grade": "B",
        },
        "drift": {
            "consensus_score_drift": -16,
            "confidence_drift": -14,
            "probability_drift": -0.18,
            "certainty_drift": -20,
            "consensus_side_changed": True,
            "stability_changed": True,
            "grade_changed": True,
        },
    }

    minor_session = {
        "ticker": "DRIFT-MINOR",
        "previous_snapshot": {
            "consensus_side": "YES",
            "consensus_score_pct": 88,
            "adjusted_confidence": 84,
            "research_stability": "high",
            "final_research_grade": "A-",
        },
        "current_snapshot": {
            "consensus_side": "YES",
            "consensus_score_pct": 91,
            "adjusted_confidence": 87,
            "research_stability": "high",
            "final_research_grade": "A-",
        },
        "drift": {
            "consensus_score_drift": 3,
            "confidence_drift": 3,
            "probability_drift": 0.01,
            "certainty_drift": 0,
            "consensus_side_changed": False,
            "stability_changed": False,
            "grade_changed": False,
        },
    }

    critical = research_drift_detection_engine.detect_session_drift(critical_session)
    assert critical["status"] == "ok"
    assert critical["read_only"] is True
    assert critical["drift_severity"] == "critical"
    assert critical["notification_priority"] == "immediate"
    assert "consensus_side_flip" in critical["reason_codes"]

    minor = research_drift_detection_engine.detect_session_drift(minor_session)
    assert minor["drift_severity"] == "minor"
    assert minor["notification_priority"] == "low"

    portfolio = research_drift_detection_engine.detect_portfolio_drift({
        "sessions": [minor_session, critical_session]
    })
    assert portfolio["status"] == "ok"
    assert portfolio["sessions_analyzed"] == 2
    assert portfolio["top_drifts"][0]["ticker"] == "DRIFT-CRITICAL"
    assert portfolio["severity_counts"]["critical"] == 1

    status = research_drift_detection_engine.status()
    assert status["status"] == "ok"

    print("[PASS] OI-064 Research Drift Detection Engine")
    print({
        "critical": critical["summary"],
        "minor": minor["summary"],
        "severity_counts": portfolio["severity_counts"],
    })


if __name__ == "__main__":
    test_oi_064_research_drift_detection_engine()
