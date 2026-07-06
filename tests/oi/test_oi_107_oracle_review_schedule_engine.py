
from qseries_v2.oracle_intelligence.oracle_review_schedule_engine import oracle_review_schedule_engine


def test_oi_107_oracle_review_schedule_engine():
    workload_balance = {
        "redistribution_plan": [
            {
                "market": "CRYPTO",
                "current_lane": "standard_monitoring",
                "current_lane_status": "normal",
                "route_priority": "immediate",
                "priority_score": 88,
                "suggested_lane": "systemic_risk_review",
                "redistribution_needed": True,
            },
            {
                "market": "NASDAQ",
                "current_lane": "alert_review",
                "current_lane_status": "hot",
                "route_priority": "priority",
                "priority_score": 72.94,
                "suggested_lane": "alert_review",
                "redistribution_needed": False,
            },
            {
                "market": "AI-SECTOR",
                "current_lane": "alert_review",
                "current_lane_status": "hot",
                "route_priority": "watch",
                "priority_score": 35,
                "suggested_lane": "standard_monitoring",
                "redistribution_needed": True,
            },
        ]
    }

    attention_routes = {
        "routes": [
            {
                "market": "CRYPTO",
                "attention_lane": "standard_monitoring",
                "route_priority": "immediate",
                "priority_score": 88,
                "top_alert_priority": "critical",
                "alert_count": 2,
                "anomaly_count": 2,
            },
            {
                "market": "NASDAQ",
                "attention_lane": "alert_review",
                "route_priority": "priority",
                "priority_score": 72.94,
                "top_alert_priority": "high",
                "alert_count": 1,
                "anomaly_count": 1,
            },
            {
                "market": "AI-SECTOR",
                "attention_lane": "alert_review",
                "route_priority": "watch",
                "priority_score": 35,
                "top_alert_priority": "none",
                "alert_count": 0,
                "anomaly_count": 0,
            },
        ]
    }

    report = oracle_review_schedule_engine.build_review_schedule(workload_balance, attention_routes)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["schedule_count"] == 3
    assert report["schedule"][0]["schedule_rank"] == 1
    assert report["schedule"][0]["review_cadence"] == "immediate"
    assert report["summary"]["review_now_count"] == 1
    assert report["summary"]["top_market"] == "CRYPTO"

    diag = oracle_review_schedule_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-107 Oracle Review Schedule Engine")
    print({
        "schedule_count": report["schedule_count"],
        "summary": report["summary"],
        "top": report["schedule"][0],
    })


if __name__ == "__main__":
    test_oi_107_oracle_review_schedule_engine()
