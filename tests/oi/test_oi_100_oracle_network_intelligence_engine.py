
from qseries_v2.oracle_intelligence.oracle_network_intelligence_engine import oracle_network_intelligence_engine


def test_oi_100_oracle_network_intelligence_engine():
    influence_graph = {"nodes": [{"market": "NASDAQ", "role": "bridge"}, {"market": "FED-RATE", "role": "dominant_source"}]}
    stability_index = {
        "global_stability_score": 62,
        "risk_posture": "heightened_monitoring",
        "scores": [{"market": "NASDAQ", "stability_score": 50}, {"market": "FED-RATE", "stability_score": 72}],
    }
    health_dashboard = {"cards": [{"market": "NASDAQ", "health_score": 32}, {"market": "FED-RATE", "health_score": 78}]}
    anomaly_report = {"anomaly_count": 1, "anomalies": [{"markets": ["NASDAQ"], "anomaly_score": 96}]}
    recovery_forecast = {"forecasts": [{"market": "NASDAQ", "recovery_score": 40}, {"market": "FED-RATE", "recovery_score": 77}]}
    confidence_report = {"calibrated_items": [{"market": "NASDAQ", "calibrated_confidence": 68}, {"market": "FED-RATE", "calibrated_confidence": 73}]}

    network = oracle_network_intelligence_engine.build_network_intelligence(
        influence_graph, stability_index, health_dashboard, anomaly_report, recovery_forecast, confidence_report
    )

    assert network["status"] == "ok"
    assert network["read_only"] is True
    assert network["market_count"] == 2
    assert network["nodes"][0]["network_score"] >= network["nodes"][-1]["network_score"]
    assert network["summary"]["top_market"] is not None

    print("[PASS] OI-100 Oracle Network Intelligence Engine")
    print({"markets": network["market_count"], "summary": network["summary"], "top": network["nodes"][0]})


if __name__ == "__main__":
    test_oi_100_oracle_network_intelligence_engine()
