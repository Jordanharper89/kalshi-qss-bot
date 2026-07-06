from qseries_v2.oracle_intelligence.scenario_simulation_engine import ScenarioSimulationEngine


class FakeCalibrationEngine:
    def calibrate_forecast(self, live_market):
        return {
            "status": "ok",
            "market": {
                "ticker": live_market.get("ticker"),
                "category": live_market.get("category"),
                "timestamp": live_market.get("timestamp"),
            },
            "calibrated_forecasts": {
                "5": {
                    "raw_yes_up_probability": 62.5,
                    "calibrated_yes_up_probability": 62.0,
                    "reliability": {"score": 86.0, "label": "very_high"},
                    "grade": "A-",
                    "historical_error": {"mae": 3.1},
                    "confidence_interval": {"lower": 58.9, "upper": 65.1, "width": 6.2},
                },
                "15": {
                    "raw_yes_up_probability": 71.0,
                    "calibrated_yes_up_probability": 70.2,
                    "reliability": {"score": 92.0, "label": "very_high"},
                    "grade": "A",
                    "historical_error": {"mae": 2.6},
                    "confidence_interval": {"lower": 68.4, "upper": 73.6, "width": 5.2},
                },
                "30": {
                    "raw_yes_up_probability": 68.0,
                    "calibrated_yes_up_probability": 67.1,
                    "reliability": {"score": 84.0, "label": "high"},
                    "grade": "B+",
                    "historical_error": {"mae": 4.0},
                    "confidence_interval": {"lower": 64.0, "upper": 72.0, "width": 8.0},
                },
            },
            "reliability_report": {
                "overall_grade": "A-",
                "average_reliability": 87.3333,
            },
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_033_scenario_simulation_engine():
    engine = ScenarioSimulationEngine(calibration_engine=FakeCalibrationEngine())

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["calibration_engine_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "BTC-TEST",
        "category": "crypto",
        "timestamp": "2026-06-29T14:30:00+00:00",
    }

    packet = engine.simulate_market(live_market)

    assert packet["status"] == "ok"
    assert packet["market"]["ticker"] == "BTC-TEST"
    assert packet["scenarios"]["bullish_yes"]["score"] > packet["scenarios"]["bearish_yes"]["score"]
    assert packet["dominant_scenario"]["name"] in packet["scenarios"]
    assert len(packet["scenario_curve"]) == 3
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    curve = engine.scenario_curve(live_market)
    assert curve[0]["horizon_minutes"] == 5

    dominant = engine.dominant_scenario(live_market)
    assert dominant["name"]

    report = engine.scenario_report(live_market)
    assert report["dominant_scenario"]["name"]

    print("[PASS] OI-033 Scenario Simulation Engine")
    print({
        "dominant": packet["dominant_scenario"],
        "bullish_score": packet["scenarios"]["bullish_yes"]["score"],
        "curve_points": len(packet["scenario_curve"]),
    })


if __name__ == "__main__":
    test_oi_033_scenario_simulation_engine()
