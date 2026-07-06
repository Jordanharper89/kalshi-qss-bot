
from qseries_v2.oracle_intelligence.risk_posture_synthesis_engine import risk_posture_synthesis_engine


def test_oi_102_risk_posture_synthesis_engine():
    strategic = {
        "global_strategic_risk_score": 48,
        "global_outlook": "watch",
        "outlooks": [
            {"market": "NASDAQ", "strategic_risk_score": 67.26},
            {"market": "FED-RATE", "strategic_risk_score": 22.0},
        ],
    }

    network = {
        "nodes": [
            {"market": "NASDAQ", "network_score": 38},
            {"market": "FED-RATE", "network_score": 78},
        ]
    }

    stability = {
        "global_stability_score": 62,
        "risk_posture": "heightened_monitoring",
        "scores": [
            {"market": "NASDAQ", "stability_score": 50},
            {"market": "FED-RATE", "stability_score": 72},
        ],
    }

    recovery = {
        "forecasts": [
            {"market": "NASDAQ", "recovery_score": 40},
            {"market": "FED-RATE", "recovery_score": 77},
        ]
    }

    alerts = {
        "alerts": [
            {"market": "NASDAQ", "priority": "high"},
            {"market": "FED-RATE", "priority": "info"},
        ]
    }

    report = risk_posture_synthesis_engine.synthesize_posture(
        strategic,
        network,
        stability,
        recovery,
        alerts,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["market_count"] == 2
    assert report["highest_risk_postures"][0]["risk_posture_score"] >= report["highest_risk_postures"][-1]["risk_posture_score"]
    assert report["global_posture"] in {"systemic_alert", "defensive", "heightened_monitoring", "selective_risk", "normal"}

    print("[PASS] OI-102 Risk Posture Synthesis Engine")
    print({
        "markets": report["market_count"],
        "global_score": report["global_risk_posture_score"],
        "global_posture": report["global_posture"],
        "top": report["highest_risk_postures"][0],
    })


if __name__ == "__main__":
    test_oi_102_risk_posture_synthesis_engine()
