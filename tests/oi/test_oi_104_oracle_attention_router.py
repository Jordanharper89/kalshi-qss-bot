
from qseries_v2.oracle_intelligence.oracle_attention_router import oracle_attention_router


def test_oi_104_oracle_attention_router():
    priority_queue = {
        "priority_queue": [
            {
                "market": "NASDAQ",
                "priority_score": 72.94,
                "priority_tier": "high",
                "risk_posture_score": 72,
                "health_score": 32,
                "recovery_score": 40,
                "alert_count": 1,
                "anomaly_count": 1,
                "top_alert_priority": "high",
            },
            {
                "market": "AI-SECTOR",
                "priority_score": 55.2,
                "priority_tier": "elevated",
                "risk_posture_score": 68,
                "health_score": 45,
                "recovery_score": 46,
                "alert_count": 1,
                "anomaly_count": 1,
                "top_alert_priority": "elevated",
            },
            {
                "market": "FED-RATE",
                "priority_score": 22.0,
                "priority_tier": "low",
                "risk_posture_score": 24,
                "health_score": 78,
                "recovery_score": 77,
                "alert_count": 1,
                "anomaly_count": 0,
                "top_alert_priority": "info",
            },
        ]
    }

    report = oracle_attention_router.route_attention(priority_queue)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["route_count"] == 3
    assert report["routes"][0]["route_rank"] == 1
    assert report["routes"][0]["route_priority"] in {"immediate", "priority", "active", "watch", "normal"}
    assert report["summary"]["top_route"]["market"] == report["routes"][0]["market"]
    assert report["lane_counts"]

    diag = oracle_attention_router.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-104 Oracle Attention Router")
    print({
        "routes": report["route_count"],
        "lane_counts": report["lane_counts"],
        "top": report["routes"][0],
    })


if __name__ == "__main__":
    test_oi_104_oracle_attention_router()
