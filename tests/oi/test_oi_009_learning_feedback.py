from qseries_v2.oi.learning_feedback import learning_feedback_engine

performance = {
    "win_rate": 45.0,
    "avg_confidence": 82.0,
    "avg_edge": -1.5,
}

result = learning_feedback_engine.feedback(performance)

assert result["adjustments"]["recommendation"] == "tighten"
assert result["oracle_executes"] is False
assert len(result["notes"]) >= 1

print("[PASS] OI-009 Learning Feedback Engine")
print(result)
