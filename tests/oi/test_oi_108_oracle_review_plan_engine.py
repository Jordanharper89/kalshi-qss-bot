
from qseries_v2.oracle_intelligence.oracle_review_plan_engine import oracle_review_plan_engine


def test_oi_108_oracle_review_plan_engine():
    review_schedule = {
        "schedule": [
            {
                "market": "CRYPTO",
                "review_cadence": "immediate",
                "review_bucket": "review_now",
                "priority_score": 88,
                "route_priority": "immediate",
                "current_lane": "standard_monitoring",
                "suggested_lane": "systemic_risk_review",
                "redistribution_needed": True,
                "alert_count": 2,
                "anomaly_count": 2,
                "top_alert_priority": "critical",
            },
            {
                "market": "NASDAQ",
                "review_cadence": "hourly",
                "review_bucket": "same_day_review",
                "priority_score": 72.94,
                "route_priority": "priority",
                "current_lane": "alert_review",
                "suggested_lane": "alert_review",
                "redistribution_needed": False,
                "alert_count": 1,
                "anomaly_count": 1,
                "top_alert_priority": "high",
            },
            {
                "market": "AI-SECTOR",
                "review_cadence": "frequent",
                "review_bucket": "active_rotation",
                "priority_score": 35,
                "route_priority": "watch",
                "current_lane": "alert_review",
                "suggested_lane": "standard_monitoring",
                "redistribution_needed": True,
                "alert_count": 0,
                "anomaly_count": 0,
                "top_alert_priority": "none",
            },
        ]
    }

    lane_status = {
        "lanes": [
            {"attention_lane": "systemic_risk_review", "lane_status": "active"},
            {"attention_lane": "alert_review", "lane_status": "hot"},
            {"attention_lane": "standard_monitoring", "lane_status": "normal"},
        ]
    }

    report = oracle_review_plan_engine.build_review_plan(review_schedule, lane_status)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["plan_count"] == 3
    assert report["review_plan"][0]["review_order"] == 1
    assert report["review_plan"][0]["market"] == "CRYPTO"
    assert report["review_plan"][0]["review_depth"] == "deep"
    assert "review_systemic_risk_contagion" in report["review_plan"][0]["checklist"]
    assert report["summary"]["deep_review_count"] >= 1

    diag = oracle_review_plan_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-108 Oracle Review Plan Engine")
    print({
        "plan_count": report["plan_count"],
        "summary": report["summary"],
        "top": report["review_plan"][0],
    })


if __name__ == "__main__":
    test_oi_108_oracle_review_plan_engine()
