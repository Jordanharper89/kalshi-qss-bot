
from qseries_v2.oracle_intelligence.oracle_review_result_engine import oracle_review_result_engine


def test_oi_109_oracle_review_result_engine():
    review_plan = {
        "review_plan": [
            {
                "market": "CRYPTO",
                "review_order": 1,
                "review_depth": "deep",
                "assigned_lane": "systemic_risk_review",
                "review_cadence": "immediate",
                "priority_score": 88,
                "alert_count": 2,
                "anomaly_count": 2,
                "checklist": [
                    "review_latest_oracle_snapshot",
                    "confirm_read_only_context",
                    "review_priority_queue_context",
                    "review_risk_posture_synthesis",
                    "review_systemic_risk_contagion",
                    "review_global_market_stability",
                    "review_active_alerts",
                    "review_alert_evidence",
                    "review_cross_market_anomalies",
                    "compare_previous_snapshot",
                    "produce_oracle_read_only_note",
                ],
            },
            {
                "market": "NASDAQ",
                "review_order": 2,
                "review_depth": "standard",
                "assigned_lane": "alert_review",
                "review_cadence": "hourly",
                "priority_score": 72.94,
                "alert_count": 1,
                "anomaly_count": 1,
                "checklist": [
                    "review_latest_oracle_snapshot",
                    "confirm_read_only_context",
                    "review_priority_queue_context",
                    "review_active_alerts",
                    "review_alert_evidence",
                    "produce_oracle_read_only_note",
                ],
            },
        ]
    }

    evidence = {
        "markets": {
            "CRYPTO": {
                "priority_score": 88,
                "risk_posture_score": 90,
                "contagion_score": 85,
                "stability_score": 30,
                "health_score": 25,
                "recovery_score": 30,
                "alert_count": 2,
                "anomaly_count": 2,
                "top_alert_priority": "critical",
                "previous_score": 48,
            },
            "NASDAQ": {
                "priority_score": 72.94,
                "health_score": 32,
                "stability_score": 50,
                "recovery_score": 40,
                "alert_count": 1,
                "anomaly_count": 1,
                "top_alert_priority": "high",
            },
        }
    }

    report = oracle_review_result_engine.build_review_results(review_plan, evidence)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["result_count"] == 2
    assert report["review_results"][0]["signal_quality_score"] >= report["review_results"][-1]["signal_quality_score"]
    assert report["summary"]["result_count"] == 2
    assert report["review_results"][0]["market"] == "CRYPTO"

    diag = oracle_review_result_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-109 Oracle Review Result Engine")
    print({
        "results": report["result_count"],
        "summary": report["summary"],
        "top": report["review_results"][0],
    })


if __name__ == "__main__":
    test_oi_109_oracle_review_result_engine()
