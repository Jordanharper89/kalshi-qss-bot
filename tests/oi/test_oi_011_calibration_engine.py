from qseries_v2.oi.calibration_engine import calibration_engine

feedback = {
    "adjustments": {
        "confidence_bias": -8.0,
        "edge_threshold_bias": 3.0,
    }
}

settings = calibration_engine.apply_feedback(feedback)

assert settings["confidence_bias"] == -8.0
assert settings["edge_threshold_bias"] == 3.0
assert settings["active_min_edge"] == 10.0
assert settings["oracle_executes"] is False

adjusted = calibration_engine.adjusted_confidence(90)

assert adjusted == 82.0

print("[PASS] OI-011 Calibration Engine")
print(settings)
print("Adjusted confidence:", adjusted)
