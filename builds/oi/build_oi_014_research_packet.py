"""
build_oi_014_research_packet.py
OI-014 Research Packet Engine Installer
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


packet_code = '''"""
OI-014 Research Packet Engine

Creates a structured packet containing the full Oracle decision output:
decision, recommendation, explanation, report, evidence, and metadata.
"""

from datetime import datetime
from .research_report import research_report_engine


class ResearchPacketEngine:

    def create(self, decision, evidence=None):
        evidence = evidence or []
        recommendation = decision.get("recommendation", {})
        report = research_report_engine.generate(decision)

        packet = {
            "packet_type": "oracle_research_packet",
            "created_at": datetime.utcnow().isoformat(),
            "ticker": decision.get("ticker"),
            "action": recommendation.get("action"),
            "confidence": recommendation.get("confidence"),
            "fair_yes_price": recommendation.get("fair_yes_price"),
            "market_yes_price": recommendation.get("market_yes_price"),
            "edge": recommendation.get("edge"),
            "reason": recommendation.get("reason"),
            "decision": decision,
            "recommendation": recommendation,
            "explanation": decision.get("explanation"),
            "report": report,
            "evidence_count": len(evidence),
            "evidence": [
                {
                    "source": getattr(item, "source", "unknown"),
                    "category": getattr(item, "category", "unknown"),
                    "value": getattr(item, "value", {}),
                    "timestamp": getattr(item, "timestamp", ""),
                }
                for item in evidence
            ],
            "oracle_executes": False,
        }

        return packet


research_packet_engine = ResearchPacketEngine()
'''

test_code = '''from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.calibrated_pipeline import calibrated_decision_pipeline
from qseries_v2.oi.research_packet import research_packet_engine

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

packet = research_packet_engine.create(decision, evidence)

assert packet["packet_type"] == "oracle_research_packet"
assert packet["ticker"] == "TEST-MARKET"
assert packet["evidence_count"] == 3
assert packet["oracle_executes"] is False
assert "ORACLE RESEARCH REPORT" in packet["report"]

print("[PASS] OI-014 Research Packet Engine")
print({
    "ticker": packet["ticker"],
    "action": packet["action"],
    "confidence": packet["confidence"],
    "evidence_count": packet["evidence_count"],
    "oracle_executes": packet["oracle_executes"],
})
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
from .research_packet import research_packet_engine, ResearchPacketEngine
'''

print("=" * 40)
print(" OI-014 INSTALLER")
print(" Research Packet Engine")
print("=" * 40)

write(OI / "research_packet.py", packet_code)
write(OI / "__init__.py", init_code)
write(ROOT / "test_oi_014_research_packet.py", test_code)

print("\n[DONE] OI-014 installed")
print("\nRun:")
print("python test_oi_014_research_packet.py")