
from qseries_v2.oracle_intelligence.market_recovery_forecast_engine import market_recovery_forecast_engine


def test_oi_098_market_recovery_forecast_engine():
    health_dashboard = {"cards": [{"market": "NASDAQ", "health_score": 32}, {"market": "FED-RATE", "health_score": 78}]}
    resilience_report = {"scores": [{"market": "NASDAQ", "resilience_score": 35}, {"market": "FED-RATE", "resilience_score": 78}]}
    stability_index = {"scores": [{"market": "NASDAQ", "stability_score": 50, "risk_pressure_score": 82, "persistence_penalty": 71}, {"market": "FED-RATE", "stability_score": 72, "risk_pressure_score": 35, "persistence_penalty": 30}]}
    anomaly_report = {"anomalies": [{"markets": ["NASDAQ"], "anomaly_score": 78, "severity": "high"}]}
    alert_report = {"alerts": [{"market": "NASDAQ", "priority": "high"}, {"market": "FED-RATE", "priority": "info"}]}

    report = market_recovery_forecast_engine.forecast_recovery(health_dashboard, resilience_report, stability_index, anomaly_report, alert_report)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["market_count"] == 2
    assert report["forecasts"][0]["recovery_score"] >= report["forecasts"][-1]["recovery_score"]
    assert any(f["market"] == "NASDAQ" for f in report["forecasts"])

    print("[PASS] OI-098 Market Recovery Forecast Engine")
    print({"markets": report["market_count"], "phases": report["phase_counts"], "top": report["forecasts"][0]})


if __name__ == "__main__":
    test_oi_098_market_recovery_forecast_engine()
