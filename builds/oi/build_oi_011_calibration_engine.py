"""
build_oi_011_calibration_engine.py
OI-011 Calibration Engine Installer
"""

from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
OI = ROOT / "qseries_v2" / "oi"


def backup(path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = path.with_suffix(path.suffix + f".bak_{stamp}")
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup(path)
    path.write_text(text, encoding="utf-8")
    print(f"[OK] Wrote {path.relative_to(ROOT)}")


calibration_code = '''"""
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
'''

test_code = '''from qseries_v2.oi.calibration_engine import calibration_engine

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
'''

init_code = '''from .evidence_engine import evidence_engine, EvidenceEngine, Evidence
from .confidence_engine import confidence_engine, ConfidenceEngine
from .probability_engine import probability_engine, ProbabilityEngine
from .recommendation_engine import recommendation_engine, RecommendationEngine
from .explanation_engine import explanation_engine, ExplanationEngine
from .decision_pipeline import oracle_decision_pipeline, OracleDecisionPipeline
from .learning_ledger import learning_ledger, LearningLedger, LearningRecord
from .performance_review import performance_review_engine, PerformanceReviewEngine
from .learning_feedback import learning_feedback_engine, LearningFeedbackEngine
from .learning_loop import oracle_learning_loop, OracleLearningLoop
from .calibration_engine import calibration_engine, CalibrationEngine
'''

print("=" * 40)
print(" OI-011 INSTALLER")
print(" Calibration Engine")
print("=" * 40)

write(OI / "calibration_engine.py", calibration_code)
write(OI / "__init__.py", init_code)
write(ROOT / "test_oi_011_calibration_engine.py", test_code)

print("\n[DONE] OI-011 installed")
print("\nRun:")
print("python test_oi_011_calibration_engine.py")