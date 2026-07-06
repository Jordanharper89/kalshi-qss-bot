from qseries_v2.oracle_intelligence.explainable_forecast_report_engine import ExplainableForecastReportEngine


class FakeForecastEngine:
    def forecast_market(self, live_market):
        return {
            "status": "ok",
            "market": {"ticker": live_market["ticker"], "category": live_market["category"], "timestamp": live_market["timestamp"]},
            "forecast_curve": [
                {"horizon_minutes": 5, "yes_up_probability": 62.0, "confidence_score": 85.0},
                {"horizon_minutes": 15, "yes_up_probability": 70.2, "confidence_score": 92.0},
            ],
            "overall_forecast": {
                "direction": "yes_up_bias",
                "score": 66.4,
                "confidence": "high",
                "interpretation": "Historical outcomes show a YES-up bias.",
            },
        }


class FakeCalibrationEngine:
    def calibrate_forecast(self, live_market):
        return {
            "status": "ok",
            "market": {"ticker": live_market["ticker"], "category": live_market["category"], "timestamp": live_market["timestamp"]},
            "calibrated_forecasts": {
                "15": {
                    "horizon_minutes": 15,
                    "grade": "A",
                    "calibrated_yes_up_probability": 70.2,
                    "reliability": {"score": 92.0},
                }
            },
            "reliability_report": {
                "overall_grade": "A",
                "average_reliability": 90.0,
                "average_error_band": 4.2,
                "horizons": 2,
            },
        }


class FakeScenarioEngine:
    def simulate_market(self, live_market):
        return {
            "status": "ok",
            "market": {"ticker": live_market["ticker"], "category": live_market["category"], "timestamp": live_market["timestamp"]},
            "dominant_scenario": {
                "name": "compression",
                "score": 66.7,
                "interpretation": "Compressed outcome range.",
            },
            "scenarios": {"compression": {}, "bullish_yes": {}},
            "source_reliability": {"overall_grade": "A"},
        }


def test_oi_034_explainable_forecast_report_engine():
    engine = ExplainableForecastReportEngine(
        forecast_engine=FakeForecastEngine(),
        calibration_engine=FakeCalibrationEngine(),
        scenario_engine=FakeScenarioEngine(),
    )

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["forecast_engine_ready"] is True
    assert diagnostics["calibration_engine_ready"] is True
    assert diagnostics["scenario_engine_ready"] is True

    live_market = {
        "ticker": "BTC-TEST",
        "category": "crypto",
        "timestamp": "2026-06-29T14:30:00+00:00",
    }

    report = engine.build_report(live_market)

    assert report["status"] == "ok"
    assert report["headline"]
    assert "BTC-TEST" in report["headline"]
    assert report["forecast_summary"]["direction"] == "yes_up_bias"
    assert report["calibration_summary"]["overall_grade"] == "A"
    assert report["scenario_summary"]["dominant_scenario"]["name"] == "compression"
    assert report["oracle_report_text"]
    assert report["read_only"] is True
    assert report["execution_allowed"] is False

    payload = engine.api_payload(live_market)
    assert payload["headline"]
    assert payload["read_only"] is True
    assert payload["execution_allowed"] is False

    latest = engine.latest()
    assert latest["headline"] == report["headline"]

    print("[PASS] OI-034 Explainable Forecast Report Engine")
    print({
        "headline": report["headline"],
        "grade": report["calibration_summary"]["overall_grade"],
        "dominant_scenario": report["scenario_summary"]["dominant_scenario"]["name"],
    })


if __name__ == "__main__":
    test_oi_034_explainable_forecast_report_engine()
