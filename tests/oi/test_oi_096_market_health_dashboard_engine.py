
from qseries_v2.oracle_intelligence.market_health_dashboard_engine import market_health_dashboard_engine


def test_oi_096_market_health_dashboard_engine():
    stability_index = {
        "global_stability_score": 62.6,
        "global_stability_tier": "mixed",
        "risk_posture": "heightened_monitoring",
        "scores": [
            {"market": "NASDAQ", "stability_score": 50.8},
            {"market": "FED-RATE", "stability_score": 74.5},
        ],
    }
    fragility_report = {"scores": [{"market": "NASDAQ", "fragility_score": 71.1}, {"market": "FED-RATE", "fragility_score": 28.0}]}
    resilience_report = {"scores": [{"market": "NASDAQ", "resilience_score": 35.0}, {"market": "FED-RATE", "resilience_score": 78.4}]}
    contagion_report = {"market_scores": [{"market": "NASDAQ", "systemic_importance_score": 75.1, "vulnerability_score": 83.1}, {"market": "FED-RATE", "systemic_importance_score": 52.0, "vulnerability_score": 20.0}]}
    alert_report = {"alert_count": 2, "alerts": [{"market": "NASDAQ", "priority": "high"}, {"market": "GLOBAL", "priority": "elevated"}]}

    dashboard = market_health_dashboard_engine.build_dashboard(stability_index, fragility_report, resilience_report, contagion_report, alert_report)

    assert dashboard["status"] == "ok"
    assert dashboard["read_only"] is True
    assert dashboard["market_count"] >= 2
    assert dashboard["cards"][0]["health_score"] >= dashboard["cards"][-1]["health_score"]
    assert any(c["market"] == "NASDAQ" for c in dashboard["cards"])

    print("[PASS] OI-096 Market Health Dashboard Engine")
    print({"markets": dashboard["market_count"], "summary": dashboard["dashboard_summary"], "worst": dashboard["worst_health_markets"][0]})


if __name__ == "__main__":
    test_oi_096_market_health_dashboard_engine()
