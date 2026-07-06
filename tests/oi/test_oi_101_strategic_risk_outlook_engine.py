
from qseries_v2.oracle_intelligence.strategic_risk_outlook_engine import strategic_risk_outlook_engine


def test_oi_101_strategic_risk_outlook_engine():
    network = {"nodes": [{"market": "NASDAQ", "network_score": 38}, {"market": "FED-RATE", "network_score": 76}]}
    stability = {"global_stability_score": 62, "risk_posture": "heightened_monitoring"}
    recovery = {"forecasts": [{"market": "NASDAQ", "recovery_score": 40}, {"market": "FED-RATE", "recovery_score": 78}]}
    anomalies = {"anomalies": [{"markets": ["NASDAQ"], "anomaly_score": 96}]}
    alerts = {"alerts": [{"market": "NASDAQ", "priority": "high"}, {"market": "FED-RATE", "priority": "info"}]}

    report = strategic_risk_outlook_engine.build_outlook(network, stability, recovery, anomalies, alerts)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["market_count"] == 2
    assert report["highest_risk_markets"][0]["strategic_risk_score"] >= report["highest_risk_markets"][-1]["strategic_risk_score"]
    assert report["global_outlook"] in {"critical_risk", "high_risk", "elevated_risk", "watch", "constructive"}

    print("[PASS] OI-101 Strategic Risk Outlook Engine")
    print({"markets": report["market_count"], "global": report["global_outlook"], "top": report["highest_risk_markets"][0]})


if __name__ == "__main__":
    test_oi_101_strategic_risk_outlook_engine()
