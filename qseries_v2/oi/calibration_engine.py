"""
OI-011 Calibration Engine

Applies learning feedback to adjust Oracle confidence and edge thresholds.
Oracle learns, but Oracle never executes trades.
"""

class CalibrationEngine:

    def __init__(self):
        self.base_min_confidence = 55.0
        self.base_min_edge = 7.0
        self.confidence_bias = 0.0
        self.edge_threshold_bias = 0.0

    def apply_feedback(self, feedback):
        adjustments = feedback.get("adjustments", {})

        self.confidence_bias += float(adjustments.get("confidence_bias", 0.0))
        self.edge_threshold_bias += float(adjustments.get("edge_threshold_bias", 0.0))

        self.confidence_bias = max(-25.0, min(25.0, self.confidence_bias))
        self.edge_threshold_bias = max(-10.0, min(10.0, self.edge_threshold_bias))

        return self.settings()

    def adjusted_confidence(self, raw_confidence):
        return round(
            max(0.0, min(100.0, float(raw_confidence) + self.confidence_bias)),
            2,
        )

    def min_confidence(self):
        return round(max(0.0, min(100.0, self.base_min_confidence - self.confidence_bias)), 2)

    def min_edge(self):
        return round(max(0.0, self.base_min_edge + self.edge_threshold_bias), 2)

    def settings(self):
        return {
            "base_min_confidence": self.base_min_confidence,
            "base_min_edge": self.base_min_edge,
            "confidence_bias": round(self.confidence_bias, 2),
            "edge_threshold_bias": round(self.edge_threshold_bias, 2),
            "active_min_confidence": self.min_confidence(),
            "active_min_edge": self.min_edge(),
            "oracle_executes": False,
        }


calibration_engine = CalibrationEngine()
