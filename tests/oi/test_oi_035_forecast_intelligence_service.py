from qseries_v2.oracle_intelligence.forecast_intelligence_service import ForecastIntelligenceService


class FakeForecast:
    def forecast_market(self, live_market):
        return {
            "status": "ok",
            "market": live_market,
            "overall_forecast": {"direction": "yes_up_bias", "score": 68.2},
            "forecast_curve": [{"horizon_minutes": 15, "yes_up_probability": 70.6}],
        }


class FakeCalibration:
    def calibrate_forecast(self, live_market):
        return {
            "status": "ok",
            "market": live_market,
            "reliability_report": {"overall_grade": "A", "average_reliability": 90.0},
        }


class FakeScenario:
    def simulate_market(self, live_market):
        return {
            "status": "ok",
            "market": live_market,
            "dominant_scenario": {"name": "compression", "score": 66.7},
        }


class FakeReport:
    def build_report(self, live_market):
        return {
            "status": "ok",
            "market": live_market,
            "headline": "BTC-TEST: yes_up_bias | Grade A | Scenario compression",
            "oracle_report_text": "Forecast report text.",
        }


def test_oi_035_forecast_intelligence_service():
    service = ForecastIntelligenceService(
        forecast_engine=FakeForecast(),
        calibration_engine=FakeCalibration(),
        scenario_engine=FakeScenario(),
        report_engine=FakeReport(),
    )

    diagnostics = service.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["forecast_engine_ready"] is True
    assert diagnostics["calibration_engine_ready"] is True
    assert diagnostics["scenario_engine_ready"] is True
    assert diagnostics["report_engine_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "BTC-TEST",
        "category": "crypto",
        "timestamp": "2026-06-29T14:30:00+00:00",
    }

    packet = service.analyze(live_market)
    assert packet["status"] == "ok"
    assert packet["api_summary"]["forecast_direction"] == "yes_up_bias"
    assert packet["api_summary"]["overall_grade"] == "A"
    assert packet["api_summary"]["dominant_scenario"] == "compression"
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    payload = service.api_payload(live_market)
    assert payload["summary"]["forecast_score"] == 68.2
    assert payload["headline"]

    latest = service.latest()
    assert latest["status"] == "ok"

    print("[PASS] OI-035 Forecast Intelligence Service")
    print({
        "headline": payload["headline"],
        "summary": payload["summary"],
    })


if __name__ == "__main__":
    test_oi_035_forecast_intelligence_service()
