from qseries_v2.oracle_intelligence.oracle_intelligence_notification_engine import OracleIntelligenceNotificationEngine


def test_oi_065_oracle_intelligence_notification_engine():
    engine = OracleIntelligenceNotificationEngine()

    drift = {
        "ticker": "NOTIFY-TEST",
        "drift_severity": "critical",
        "notification_priority": "immediate",
        "reason_codes": ["consensus_side_flip", "major_confidence_drift"],
        "summary": {
            "headline": "NOTIFY-TEST: CRITICAL research drift detected",
            "consensus_side": "NO",
            "previous_consensus_side": "YES",
            "consensus_score_drift": -18,
            "confidence_drift": -12,
            "probability_drift": -0.19,
            "certainty_drift": -20,
            "current_grade": "B",
            "previous_grade": "A",
            "current_stability": "low",
            "previous_stability": "high",
        },
    }

    notification = engine.build_notification(drift, channel="telegram")
    assert notification["status"] == "ok"
    assert notification["read_only"] is True
    assert notification["should_send"] is True
    assert "Oracle Research Drift Alert" in notification["message"]
    assert notification["payload"]["execution_enabled"] is False

    duplicate = engine.build_notification(drift, channel="telegram")
    assert duplicate["should_send"] is False

    forced = engine.build_notification(drift, channel="api", force=True)
    assert forced["should_send"] is True
    assert "severity=critical" in forced["message"]

    portfolio = engine.build_portfolio_notifications({
        "top_drifts": [
            drift,
            {
                "ticker": "NO-DRIFT",
                "drift_severity": "none",
                "notification_priority": "silent",
                "reason_codes": ["no_material_drift"],
                "summary": {"headline": "NO-DRIFT: No material research drift"},
            },
        ]
    }, force=True)

    assert portfolio["status"] == "ok"
    assert portfolio["notification_count"] == 2

    history = engine.notification_history()
    assert history["count"] >= 2

    status = engine.status()
    assert status["status"] == "ok"

    print("[PASS] OI-065 Oracle Intelligence Notification Engine")
    print({
        "sent": notification["should_send"],
        "duplicate_sent": duplicate["should_send"],
        "history_count": history["count"],
    })


if __name__ == "__main__":
    test_oi_065_oracle_intelligence_notification_engine()
