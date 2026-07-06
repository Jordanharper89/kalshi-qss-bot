"""
build_oi_009_learning_feedback.py
OI-009 Learning Feedback Engine Installer
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


feedback_code = '''"""
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
'''

test_code = '''from qseries_v2.oi.learning_feedback import learning_feedback_engine

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
'''

print("=" * 40)
print(" OI-009 INSTALLER")
print(" Learning Feedback Engine")
print("=" * 40)

write(OI / "learning_feedback.py", feedback_code)
write(OI / "__init__.py", init_code)
write(ROOT / "test_oi_009_learning_feedback.py", test_code)

print("\n[DONE] OI-009 installed")
print("\nRun:")
print("python test_oi_009_learning_feedback.py")