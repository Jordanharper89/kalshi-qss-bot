
from qseries_v2.oracle_intelligence.attention_lane_status_engine import attention_lane_status_engine


def test_oi_105_attention_lane_status_engine():
    routes = {
        "routes": [
            {
                "market": "NASDAQ",
                "attention_lane": "alert_review",
                "route_priority": "priority",
                "priority_score": 72.94,
            },
            {
                "market": "AI-SECTOR",
                "attention_lane": "alert_review",
                "route_priority": "active",
                "priority_score": 55.2,
            },
            {
                "market": "CRYPTO",
                "attention_lane": "anomaly_review",
                "route_priority": "immediate",
                "priority_score": 88.0,
            },
            {
                "market": "FED-RATE",
                "attention_lane": "standard_monitoring",
                "route_priority": "normal",
                "priority_score": 22.0,
            },
        ]
    }

    report = attention_lane_status_engine.build_lane_status(routes)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["lane_count"] == 3
    assert report["lanes"][0]["load_score"] >= report["lanes"][-1]["load_score"]
    assert report["summary"]["total_routes"] == 4
    assert report["summary"]["top_lane"] is not None

    diag = attention_lane_status_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-105 Attention Lane Status Engine")
    print({
        "lanes": report["lane_count"],
        "summary": report["summary"],
        "top": report["lanes"][0],
    })


if __name__ == "__main__":
    test_oi_105_attention_lane_status_engine()
