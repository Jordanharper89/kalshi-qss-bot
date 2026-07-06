
from qseries_v2.oracle_intelligence.market_priority_queue_engine import market_priority_queue_engine


def test_oi_103_market_priority_queue_engine():
    risk_posture = {
        "postures": [
            {"market": "NASDAQ", "risk_posture_score": 72},
            {"market": "FED-RATE", "risk_posture_score": 24},
            {"market": "AI-SECTOR", "risk_posture_score": 68},
        ]
    }

    alerts = {
        "alerts": [
            {"market": "NASDAQ", "priority": "high"},
            {"market": "AI-SECTOR", "priority": "elevated"},
            {"market": "FED-RATE", "priority": "info"},
        ]
    }

    anomalies = {
        "anomalies": [
            {"markets": ["NASDAQ"], "anomaly_score": 96},
            {"markets": ["AI-SECTOR"], "anomaly_score": 58},
        ]
    }

    health = {
        "cards": [
            {"market": "NASDAQ", "health_score": 32},
            {"market": "FED-RATE", "health_score": 78},
            {"market": "AI-SECTOR", "health_score": 45},
        ]
    }

    recovery = {
        "forecasts": [
            {"market": "NASDAQ", "recovery_score": 40},
            {"market": "FED-RATE", "recovery_score": 77},
            {"market": "AI-SECTOR", "recovery_score": 46},
        ]
    }

    report = market_priority_queue_engine.build_priority_queue(
        risk_posture,
        alerts,
        anomalies,
        health,
        recovery,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["queue_count"] == 3
    assert report["priority_queue"][0]["rank"] == 1
    assert report["priority_queue"][0]["priority_score"] >= report["priority_queue"][-1]["priority_score"]
    assert report["queue_summary"]["top_market"] == report["priority_queue"][0]["market"]

    diag = market_priority_queue_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-103 Market Priority Queue Engine")
    print({
        "queue_count": report["queue_count"],
        "summary": report["queue_summary"],
        "top": report["priority_queue"][0],
    })


if __name__ == "__main__":
    test_oi_103_market_priority_queue_engine()
