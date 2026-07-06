"""
build_oi_010_learning_loop.py
OI-010 Oracle Learning Loop Installer
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


loop_code = '''"""
OI-010 Oracle Learning Loop

Connects:
Learning Ledger -> Performance Review -> Learning Feedback

This closes Oracle's first measurable learning cycle.
Oracle learns from resolved markets but never executes trades.
"""

from .performance_review import performance_review_engine
from .learning_feedback import learning_feedback_engine


class OracleLearningLoop:

    def run(self, records):
        performance = performance_review_engine.review(records)
        feedback = learning_feedback_engine.feedback(performance)

        return {
            "performance": performance,
            "feedback": feedback,
            "oracle_executes": False,
        }


oracle_learning_loop = OracleLearningLoop()
'''

test_code = '''from qseries_v2.oi.learning_ledger import LearningLedger
from qseries_v2.oi.learning_loop import oracle_learning_loop

ledger = LearningLedger()

rec1 = {
    "ticker": "TEST-1",
    "action": "BUY_YES",
    "confidence": 90,
    "fair_yes_price": 90,
    "market_yes_price": 80,
    "edge": 10,
}

rec2 = {
    "ticker": "TEST-2",
    "action": "BUY_YES",
    "confidence": 82,
    "fair_yes_price": 82,
    "market_yes_price": 76,
    "edge": 6,
}

ledger.record_recommendation(rec1)
ledger.record_recommendation(rec2)

ledger.resolve("TEST-1", "YES")
ledger.resolve("TEST-2", "NO")

result = oracle_learning_loop.run(ledger.records)

assert result["performance"]["total_records"] == 2
assert result["performance"]["wins"] == 1
assert result["performance"]["losses"] == 1
assert result["oracle_executes"] is False
assert "adjustments" in result["feedback"]

print("[PASS] OI-010 Oracle Learning Loop")
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
from .learning_loop import oracle_learning_loop, OracleLearningLoop
'''

print("=" * 40)
print(" OI-010 INSTALLER")
print(" Oracle Learning Loop")
print("=" * 40)

write(OI / "learning_loop.py", loop_code)
write(OI / "__init__.py", init_code)
write(ROOT / "test_oi_010_learning_loop.py", test_code)

print("\n[DONE] OI-010 installed")
print("\nRun:")
print("python test_oi_010_learning_loop.py")