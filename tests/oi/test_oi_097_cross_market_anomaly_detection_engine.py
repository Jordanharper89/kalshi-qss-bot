
from qseries_v2.oracle_intelligence.cross_market_anomaly_detection_engine import cross_market_anomaly_detection_engine


def test_oi_097_cross_market_anomaly_detection_engine():
    current_dashboard = {"cards": [{"market": "NASDAQ", "health_score": 32}, {"market": "FED-RATE", "health_score": 78}, {"market": "AI-SECTOR", "health_score": 72}]}
    previous_dashboard = {"cards": [{"market": "NASDAQ", "health_score": 55}, {"market": "FED-RATE", "health_score": 76}, {"market": "AI-SECTOR", "health_score": 70}]}
    influence_graph = {"edges": [{"source": "FED-RATE", "target": "NASDAQ", "influence_score": 83}]}
    transition_graph = {"nodes": [{"market": "AI-SECTOR", "regime": "stress"}, {"market": "NASDAQ", "regime": "contraction"}]}
    alert_report = {"alerts": [{"market": "AI-SECTOR", "priority": "high", "alert_type": "persistent_risk_pressure"}]}

    report = cross_market_anomaly_detection_engine.detect_anomalies(current_dashboard, previous_dashboard, influence_graph, transition_graph, alert_report)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["anomaly_count"] >= 3
    assert report["anomalies"][0]["anomaly_score"] >= report["anomalies"][-1]["anomaly_score"]

    print("[PASS] OI-097 Cross-Market Anomaly Detection Engine")
    print({"anomalies": report["anomaly_count"], "summary": report["summary"], "top": report["anomalies"][0]})


if __name__ == "__main__":
    test_oi_097_cross_market_anomaly_detection_engine()
