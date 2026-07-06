from qseries_v2.oracle_intelligence.confidence_calibration_engine import ConfidenceCalibrationEngine


class FakeForecastEngine:
    def forecast_market(self, live_market):
        return {
            "status": "ok",
            "market": {
                "ticker": live_market.get("ticker"),
                "category": live_market.get("category"),
                "timestamp": live_market.get("timestamp"),
            },
            "horizon_forecasts": {
                "5": {
                    "yes_up_probability": 62.5,
                    "expected_yes_change": 0.25,
                    "confidence": {
                        "score": 85.0,
                        "label": "very_high",
                        "sample_size": 80,
                        "consistency": 91.0,
                    },
                },
                "15": {
                    "yes_up_probability": 71.0,
                    "expected_yes_change": 0.75,
                    "confidence": {
                        "score": 92.0,
                        "label": "very_high",
                        "sample_size": 90,
                        "consistency": 94.0,
                    },
                },
                "30": {
                    "yes_up_probability": 68.0,
                    "expected_yes_change": 1.1,
                    "confidence": {
                        "score": 82.0,
                        "label": "high",
                        "sample_size": 60,
                        "consistency": 86.0,
                    },
                },
            },
            "forecast_curve": [],
            "overall_forecast": {
                "direction": "yes_up_bias",
                "score": 67.5,
                "confidence": "high",
            },
            "source_confidence": {
                "score": 90.0,
                "label": "very_high",
            },
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_032_confidence_calibration_engine():
    engine = ConfidenceCalibrationEngine(forecast_engine=FakeForecastEngine())

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["forecast_engine_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "BTC-TEST",
        "category": "crypto",
        "timestamp": "2026-06-29T14:30:00+00:00",
    }

    packet = engine.calibrate_forecast(live_market)

    assert packet["status"] == "ok"
    assert packet["market"]["ticker"] == "BTC-TEST"
    assert packet["calibrated_forecasts"]
    assert packet["calibrated_forecasts"]["15"]["grade"] in {"A+", "A", "A-", "B+"}
    assert packet["calibrated_forecasts"]["15"]["confidence_interval"]["lower"] < 71.0
    assert packet["calibrated_forecasts"]["15"]["confidence_interval"]["upper"] > 71.0
    assert packet["reliability_report"]["overall_grade"] in {"A+", "A", "A-", "B+", "B"}
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    grade = engine.forecast_grade(live_market, 15)
    assert grade["grade"] in {"A+", "A", "A-", "B+"}

    interval = engine.confidence_interval(live_market, 15)
    assert interval["confidence_interval"]["lower"] < interval["confidence_interval"]["upper"]

    report = engine.reliability_report(live_market)
    assert report["horizons"] == 3

    snapshot = engine.calibration_snapshot()
    assert snapshot["module"] == "oracle_calibration_snapshot"

    print("[PASS] OI-032 Confidence Calibration Engine")
    print({
        "overall_grade": packet["reliability_report"]["overall_grade"],
        "h15_grade": packet["calibrated_forecasts"]["15"]["grade"],
        "h15_interval": packet["calibrated_forecasts"]["15"]["confidence_interval"],
    })


if __name__ == "__main__":
    test_oi_032_confidence_calibration_engine()
