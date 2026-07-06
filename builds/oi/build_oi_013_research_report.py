"""
build_oi_013_research_report.py
OI-013 Research Report Engine Installer
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


report_code = '''"""
OI-013 Research Report Engine

Produces a clean Oracle research report from a decision pipeline result.
Oracle researches, scores, explains, and learns.
Oracle does not execute trades.
"""

class ResearchReportEngine:

    def generate(self, decision):
        rec = decision.get("recommendation", {})
        calibration = decision.get("calibration", {})

        lines = []
        lines.append("ORACLE RESEARCH REPORT")
        lines.append("=" * 40)
        lines.append(f"Ticker: {decision.get('ticker')}")
        lines.append(f"Action: {rec.get('action')}")
        lines.append(f"Confidence: {rec.get('confidence')}%")
        lines.append(f"Market YES Price: {rec.get('market_yes_price')}")
        lines.append(f"Oracle Fair YES Price: {rec.get('fair_yes_price')}")
        lines.append(f"Edge: {rec.get('edge')}")
        lines.append("")
        lines.append("Reason")
        lines.append("-" * 40)
        lines.append(str(rec.get("reason")))
        lines.append("")
        lines.append("Calibration")
        lines.append("-" * 40)
        lines.append(f"Min Confidence: {calibration.get('active_min_confidence', 'n/a')}")
        lines.append(f"Min Edge: {calibration.get('active_min_edge', 'n/a')}")
        lines.append("")
        lines.append("Explanation")
        lines.append("-" * 40)
        lines.append(str(decision.get("explanation", "")))
        lines.append("")
        lines.append("Execution")
        lines.append("-" * 40)
        lines.append("Oracle does not execute trades. Q Series handles execution.")

        return "\\n".join(lines)


research_report_engine = ResearchReportEngine()
'''

test_code = '''from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.calibrated_pipeline import calibrated_decision_pipeline
from qseries_v2.oi.research_report import research_report_engine

evidence = [
    Evidence(source="Market", category="market", value={"move": "up"}),
    Evidence(source="News", category="news", value={"tone": "positive"}),
    Evidence(source="History", category="historical", value={"pattern": "matched"}),
]

decision = calibrated_decision_pipeline.run(
    ticker="TEST-MARKET",
    market_yes_price=80,
    evidence=evidence,
)

report = research_report_engine.generate(decision)

assert "ORACLE RESEARCH REPORT" in report
assert "TEST-MARKET" in report
assert "Oracle does not execute trades" in report

print("[PASS] OI-013 Research Report Engine")
print(report)
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
from .research_report import research_report_engine, ResearchReportEngine
'''

print("=" * 40)
print(" OI-013 INSTALLER")
print(" Research Report Engine")
print("=" * 40)

write(OI / "research_report.py", report_code)
write(OI / "__init__.py", init_code)
write(ROOT / "test_oi_013_research_report.py", test_code)

print("\n[DONE] OI-013 installed")
print("\nRun:")
print("python test_oi_013_research_report.py")