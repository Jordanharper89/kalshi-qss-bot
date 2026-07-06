"""
build_oi_008_performance_review.py
OI-008 Performance Review Engine Installer
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


review_code = '''"""
OI-008 Performance Review Engine

Reviews Oracle's historical recommendations and summarizes performance.
Every engine is a measurable scientific experiment.
"""

class PerformanceReviewEngine:

    def review(self, records):
        total = len(records)
        wins = sum(1 for r in records if getattr(r, "result", "") == "win")
        losses = sum(1 for r in records if getattr(r, "result", "") == "loss")
        passes = sum(1 for r in records if getattr(r, "result", "") == "pass")
        pending = sum(1 for r in records if getattr(r, "result", "") == "pending")

        resolved = wins + losses
        win_rate = round((wins / resolved) * 100, 2) if resolved else 0.0

        avg_confidence = round(
            sum(float(getattr(r, "confidence", 0)) for r in records) / total,
            2
        ) if total else 0.0

        avg_edge = round(
            sum(float(getattr(r, "edge", 0)) for r in records) / total,
            2
        ) if total else 0.0

        return {
            "total_records": total,
            "wins": wins,
            "losses": losses,
            "passes": passes,
            "pending": pending,
            "resolved": resolved,
            "win_rate": win_rate,
            "avg_confidence": avg_confidence,
            "avg_edge": avg_edge,
        }


performance_review_engine = PerformanceReviewEngine()
'''

test_code = '''from qseries_v2.oi.learning_ledger import LearningLedger
from qseries_v2.oi.performance_review import performance_review_engine

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
    "action": "BUY_NO",
    "confidence": 70,
    "fair_yes_price": 30,
    "market_yes_price": 40,
    "edge": -10,
}

ledger.record_recommendation(rec1)
ledger.record_recommendation(rec2)

ledger.resolve("TEST-1", "YES")
ledger.resolve("TEST-2", "YES")

review = performance_review_engine.review(ledger.records)

assert review["total_records"] == 2
assert review["wins"] == 1
assert review["losses"] == 1
assert review["win_rate"] == 50.0

print("[PASS] OI-008 Performance Review Engine")
print(review)
'''

init_code = '''from .evidence_engine import evidence_engine, EvidenceEngine, Evidence
from .confidence_engine import confidence_engine, ConfidenceEngine
from .probability_engine import probability_engine, ProbabilityEngine
from .recommendation_engine import recommendation_engine, RecommendationEngine
from .explanation_engine import explanation_engine, ExplanationEngine
from .decision_pipeline import oracle_decision_pipeline, OracleDecisionPipeline
from .learning_ledger import learning_ledger, LearningLedger, LearningRecord
from .performance_review import performance_review_engine, PerformanceReviewEngine
'''

print("=" * 40)
print(" OI-008 INSTALLER")
print(" Performance Review Engine")
print("=" * 40)

write(OI / "performance_review.py", review_code)
write(OI / "__init__.py", init_code)
write(ROOT / "test_oi_008_performance_review.py", test_code)

print("\n[DONE] OI-008 installed")
print("\nRun:")
print("python test_oi_008_performance_review.py")