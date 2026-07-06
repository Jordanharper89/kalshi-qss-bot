
from qseries_v2.oracle_intelligence.oracle_workload_balance_engine import oracle_workload_balance_engine


def test_oi_106_oracle_workload_balance_engine():
    lane_status = {
        "lanes": [
            {
                "attention_lane": "alert_review",
                "lane_status": "hot",
                "load_score": 72,
                "route_count": 2,
            },
            {
                "attention_lane": "standard_monitoring",
                "lane_status": "normal",
                "load_score": 18,
                "route_count": 1,
            },
            {
                "attention_lane": "anomaly_review",
                "lane_status": "active",
                "load_score": 54,
                "route_count": 1,
            },
        ]
    }

    routes = {
        "routes": [
            {
                "market": "NASDAQ",
                "attention_lane": "alert_review",
                "route_priority": "priority",
                "priority_score": 72.94,
                "top_alert_priority": "high",
                "health_score": 32,
                "recovery_score": 40,
                "alert_count": 1,
                "anomaly_count": 1,
            },
            {
                "market": "AI-SECTOR",
                "attention_lane": "alert_review",
                "route_priority": "watch",
                "priority_score": 35,
                "top_alert_priority": "none",
                "health_score": 60,
                "recovery_score": 65,
                "alert_count": 0,
                "anomaly_count": 0,
            },
            {
                "market": "CRYPTO",
                "attention_lane": "standard_monitoring",
                "route_priority": "immediate",
                "priority_score": 88,
                "top_alert_priority": "critical",
                "health_score": 25,
                "recovery_score": 30,
                "alert_count": 2,
                "anomaly_count": 2,
            },
        ]
    }

    report = oracle_workload_balance_engine.balance_workload(lane_status, routes)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["lane_count"] == 3
    assert report["route_count"] == 3
    assert report["redistribution_count"] >= 1
    assert report["lane_balance"][0]["load_score"] >= report["lane_balance"][-1]["load_score"]
    assert report["summary"]["workload_state"] in {"overloaded", "hot", "redistribution_needed", "balanced"}

    diag = oracle_workload_balance_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-106 Oracle Workload Balance Engine")
    print({
        "routes": report["route_count"],
        "redistribution": report["redistribution_count"],
        "summary": report["summary"],
        "top": report["redistribution_plan"][0],
    })


if __name__ == "__main__":
    test_oi_106_oracle_workload_balance_engine()
