"""
build_oi_006_decision_pipeline.py
OI-006 Oracle Decision Pipeline Installer
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
OI-006 Oracle Decision Pipeline

Connects:
Evidence -> Confidence -> Probability -> Recommendation -> Explanation
"""

from .confidence_engine import confidence_engine
from .probability_engine import probability_engine
from .recommendation_engine import recommendation_engine
from .explanation_engine import explanation_engine


class OracleDecisionPipeline:

    def run(self, ticker, market_yes_price, evidence):
        confidence = confidence_engine.score(evidence)
        fair_yes = probability_engine.fair_yes_price(confidence)

        recommendation = recommendation_engine.recommend(
            ticker=ticker,
            market_yes_price=market_yes_price,
            fair_yes_price=fair_yes,
            confidence=confidence,
        )

        explanation = explanation_engine.explain(
            recommendation=recommendation,
            evidence=evidence,
        )

        return {
            "ticker": ticker,
            "confidence": confidence,
            "fair_yes_price": fair_yes,
            "recommendation": recommendation,
            "explanation": explanation,
            "oracle_executes": False,
        }


oracle_decision_pipeline = OracleDecisionPipeline()
'''

test_code = '''from qseries_v2.oi.evidence_engine import Evidence
from qseries_v2.oi.decision_pipeline import oracle_decision_pipeline

evidence = [
    Evidence(source="Market", category="market", value={"move": "up"}),
    Evidence(source="News", category="news", value={"tone": "positive"}),
    Evidence(source="History", category="historical", value={"pattern": "matched"}),
]

result = oracle_decision_pipeline.run(
    ticker="TEST-MARKET",
    market_yes_price=80,
    evidence=evidence,
)

assert result["ticker"] == "TEST-MARKET"
assert result["confidence"] > 0
assert result["fair_yes_price"] > 0
assert result["recommendation"]["oracle_executes"] is False
assert "TEST-MARKET" in result["explanation"]

print("[PASS] OI-006 Oracle Decision Pipeline")
print(result["recommendation"])
print()
print(result["explanation"])
'''

init_code = '''from .evidence_engine import evidence_engine, EvidenceEngine, Evidence
from .confidence_engine import confidence_engine, ConfidenceEngine
from .probability_engine import probability_engine, ProbabilityEngine
from .recommendation_engine import recommendation_engine, RecommendationEngine
from .explanation_engine import explanation_engine, ExplanationEngine
from .decision_pipeline import oracle_decision_pipeline, OracleDecisionPipeline
'''

print("=" * 40)
print(" OI-006 INSTALLER")
print(" Oracle Decision Pipeline")
print("=" * 40)

write(OI / "decision_pipeline.py", pipeline_code)
write(OI / "__init__.py", init_code)
write(ROOT / "test_oi_006_decision_pipeline.py", test_code)

print("\n[DONE] OI-006 installed")
print("\nRun:")
print("python test_oi_006_decision_pipeline.py")