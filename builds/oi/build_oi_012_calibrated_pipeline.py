"""
build_oi_012_calibrated_pipeline.py
OI-012 Calibrated Decision Pipeline Installer
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


pipeline_code = '''"""
OI-012 Calibrated Decision Pipeline

Uses Calibration Engine to adjust confidence and edge thresholds before
Oracle produces a recommendation.
"""

from .confidence_engine import confidence_engine
from .probability_engine import probability_engine
from .recommendation_engine import recommendation_engine
from .explanation_engine import explanation_engine
from .calibration_engine import calibration_engine


class CalibratedDecisionPipeline:

    def run(self, ticker, market_yes_price, evidence):
        raw_confidence = confidence_engine.score(evidence)
        adjusted_confidence = calibration_engine.adjusted_confidence(raw_confidence)
        fair_yes = probability_engine.fair_yes_price(adjusted_confidence)

        recommendation = recommendation_engine.recommend(
            ticker=ticker,
            market_yes_price=market_yes_price,
            fair_yes_price=fair_yes,
            confidence=adjusted_confidence,
        )

        calibration = calibration_engine.settings()

        if adjusted_confidence < calibration["active_min_confidence"]:
            recommendation["action"] = "PASS"
            recommendation["reason"] = "Adjusted confidence below calibrated minimum."

        if abs(recommendation["edge"]) < calibration["active_min_edge"]:
            recommendation["action"] = "PASS"
            recommendation["reason"] = "Edge below calibrated minimum."

        explanation = explanation_engine.explain(recommendation, evidence)

        return {
            "ticker": ticker,
            "raw_confidence": raw_confidence,
            "adjusted_confidence": adjusted_confidence,
            "fair_yes_price": fair_yes,
            "calibration": calibration,
            "recommendation": recommendation,
            "explanation": explanation,
            "oracle_executes": False,
        }


calibrated_decision_pipeline = CalibratedDecisionPipeline()
'''

test_code = '''from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.calibrated_pipeline import calibrated_decision_pipeline

evidence = [
    Evidence(source="Market", category="market", value={"move": "up"}),
    Evidence(source="News", category="news", value={"tone": "positive"}),
    Evidence(source="History", category="historical", value={"pattern": "matched"}),
]

result = calibrated_decision_pipeline.run(
    ticker="TEST-MARKET",
    market_yes_price=80,
    evidence=evidence,
)

assert result["ticker"] == "TEST-MARKET"
assert result["adjusted_confidence"] > 0
assert "recommendation" in result
assert result["oracle_executes"] is False

print("[PASS] OI-012 Calibrated Decision Pipeline")
print(result["recommendation"])
print(result["calibration"])
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
from .calibrated_pipeline import calibrated_decision_pipeline, CalibratedDecisionPipeline
'''

print("=" * 40)
print(" OI-012 INSTALLER")
print(" Calibrated Decision Pipeline")
print("=" * 40)

write(OI / "calibrated_pipeline.py", pipeline_code)
write(OI / "__init__.py", init_code)
write(ROOT / "test_oi_012_calibrated_pipeline.py", test_code)

print("\n[DONE] OI-012 installed")
print("\nRun:")
print("python test_oi_012_calibrated_pipeline.py")