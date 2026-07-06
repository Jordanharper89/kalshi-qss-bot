"""
OI-009 Learning Feedback Engine

Uses performance reviews to suggest simple calibration adjustments.
Oracle learns from resolved markets, but never executes trades.
"""

class LearningFeedbackEngine:

    def feedback(self, performance):
        win_rate = float(performance.get("win_rate", 0))
        avg_confidence = float(performance.get("avg_confidence", 0))
        avg_edge = float(performance.get("avg_edge", 0))

        notes = []
        adjustments = {
            "confidence_bias": 0.0,
            "edge_threshold_bias": 0.0,
            "recommendation": "hold",
        }

        if win_rate >= 60:
            notes.append("Performance is positive. Current thresholds appear usable.")
            adjustments["recommendation"] = "maintain"
        elif win_rate < 50:
            notes.append("Performance is below target. Tighten thresholds before scaling.")
            adjustments["confidence_bias"] = -5.0
            adjustments["edge_threshold_bias"] = 2.0
            adjustments["recommendation"] = "tighten"
        else:
            notes.append("Performance is neutral. Continue collecting resolved samples.")

        if avg_confidence > 80 and win_rate < 55:
            notes.append("Confidence may be overestimated versus outcomes.")
            adjustments["confidence_bias"] -= 3.0

        if avg_edge <= 0 and win_rate < 55:
            notes.append("Average edge is weak. Require stronger price dislocation.")
            adjustments["edge_threshold_bias"] += 1.0

        return {
            "win_rate": win_rate,
            "avg_confidence": avg_confidence,
            "avg_edge": avg_edge,
            "adjustments": adjustments,
            "notes": notes,
            "oracle_executes": False,
        }


learning_feedback_engine = LearningFeedbackEngine()
