from qseries_v2.oracle_intelligence.probabilistic_forecasting_engine import ProbabilisticForecastingEngine


class FakeOutcomeEngine:
    def forward_outcomes(self, live_market):
        return {
            "status": "ok",
            "horizon_statistics": {
                "5": {
                    "observations": 80,
                    "yes_price_change": {"mean": 0.25, "positive_frequency": 62.5},
                    "no_price_change": {"mean": -0.25, "positive_frequency": 37.5},
                    "confidence": {"score": 85.0, "label": "very_high", "sample_size": 80, "consistency": 91.0},
                },
                "15": {
                    "observations": 80,
                    "yes_price_change": {"mean": 0.75, "positive_frequency": 70.0},
                    "no_price_change": {"mean": -0.75, "positive_frequency": 30.0},
                    "confidence": {"score": 88.0, "label": "very_high", "sample_size": 80, "consistency": 90.0},
                },
                "30": {
                    "observations": 75,
                    "yes_price_change": {"mean": 1.1, "positive_frequency": 72.0},
                    "no_price_change": {"mean": -1.1, "positive_frequency": 28.0},
                    "confidence": {"score": 82.0, "label": "high", "sample_size": 75, "consistency": 86.0},
                },
            },
            "confidence": {"score": 90.0, "label": "very_high", "matches_found": 100},
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_031_probabilistic_forecasting_engine():
    engine = ProbabilisticForecastingEngine(outcome_engine=FakeOutcomeEngine())

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["outcome_engine_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "BTC-TEST",
        "category": "crypto",
        "timestamp": "2026-06-29T14:30:00+00:00",
    }

    packet = engine.forecast_market(live_market)

    assert packet["status"] == "ok"
    assert packet["market"]["ticker"] == "BTC-TEST"
    assert len(packet["forecast_curve"]) == 3
    assert packet["horizon_forecasts"]["15"]["yes_up_probability"] > 50
    assert packet["overall_forecast"]["direction"] == "yes_up_bias"
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    curve = engine.forecast_curve(live_market)
    assert curve[0]["horizon_minutes"] == 5

    h15 = engine.horizon_forecast(live_market, 15)
    assert h15["horizon_minutes"] == 15
    assert h15["expected_yes_change"] == 0.75

    latest = engine.latest()
    assert latest["status"] == "ok"

    print("[PASS] OI-031 Probabilistic Forecasting Engine")
    print({
        "overall_forecast": packet["overall_forecast"],
        "curve_points": len(packet["forecast_curve"]),
        "h15_yes_up": packet["horizon_forecasts"]["15"]["yes_up_probability"],
    })


if __name__ == "__main__":
    test_oi_031_probabilistic_forecasting_engine()
