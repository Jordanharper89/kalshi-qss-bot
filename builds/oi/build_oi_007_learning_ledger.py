"""
build_oi_007_learning_ledger.py
OI-007 Learning Ledger Installer
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


ledger_code = '''"""
OI-007 Learning Ledger

Records Oracle recommendations, resolved outcomes, and performance feedback.
Oracle continuously learns from resolved markets.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LearningRecord:
    ticker: str
    action: str
    confidence: float
    fair_yes_price: float
    market_yes_price: float
    edge: float
    outcome: str = "unresolved"
    result: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved_at: str = ""


class LearningLedger:

    def __init__(self):
        self.records = []

    def record_recommendation(self, recommendation):
        record = LearningRecord(
            ticker=recommendation.get("ticker"),
            action=recommendation.get("action"),
            confidence=float(recommendation.get("confidence", 0)),
            fair_yes_price=float(recommendation.get("fair_yes_price", 0)),
            market_yes_price=float(recommendation.get("market_yes_price", 0)),
            edge=float(recommendation.get("edge", 0)),
        )
        self.records.append(record)
        return record

    def resolve(self, ticker, outcome):
        for record in self.records:
            if record.ticker == ticker and record.outcome == "unresolved":
                record.outcome = outcome
                record.resolved_at = datetime.utcnow().isoformat()

                if record.action == "PASS":
                    record.result = "pass"
                elif record.action == "BUY_YES":
                    record.result = "win" if outcome == "YES" else "loss"
                elif record.action == "BUY_NO":
                    record.result = "win" if outcome == "NO" else "loss"
                else:
                    record.result = "unknown"

                return record

        return None

    def summary(self):
        wins = sum(1 for r in self.records if r.result == "win")
        losses = sum(1 for r in self.records if r.result == "loss")
        pending = sum(1 for r in self.records if r.result == "pending")
        passes = sum(1 for r in self.records if r.result == "pass")
        total_resolved = wins + losses
        win_rate = round((wins / total_resolved) * 100, 2) if total_resolved else 0.0

        return {
            "records": len(self.records),
            "wins": wins,
            "losses": losses,
            "pending": pending,
            "passes": passes,
            "win_rate": win_rate,
        }


learning_ledger = LearningLedger()
'''

test_code = '''from qseries_v2.oi.learning_ledger import learning_ledger

recommendation = {
    "ticker": "TEST-MARKET",
    "action": "BUY_YES",
    "confidence": 91.67,
    "fair_yes_price": 91.67,
    "market_yes_price": 80.0,
    "edge": 11.67,
}

record = learning_ledger.record_recommendation(recommendation)
resolved = learning_ledger.resolve("TEST-MARKET", "YES")
summary = learning_ledger.summary()

assert record.ticker == "TEST-MARKET"
assert resolved.result == "win"
assert summary["wins"] == 1
assert summary["win_rate"] == 100.0

print("[PASS] OI-007 Learning Ledger")
print(summary)
'''

init_code = '''from .evidence_engine import evidence_engine, EvidenceEngine, Evidence
from .confidence_engine import confidence_engine, ConfidenceEngine
from .probability_engine import probability_engine, ProbabilityEngine
from .recommendation_engine import recommendation_engine, RecommendationEngine
from .explanation_engine import explanation_engine, ExplanationEngine
from .decision_pipeline import oracle_decision_pipeline, OracleDecisionPipeline
from .learning_ledger import learning_ledger, LearningLedger, LearningRecord
'''

print("=" * 40)
print(" OI-007 INSTALLER")
print(" Learning Ledger")
print("=" * 40)

write(OI / "learning_ledger.py", ledger_code)
write(OI / "__init__.py", init_code)
write(ROOT / "test_oi_007_learning_ledger.py", test_code)

print("\n[DONE] OI-007 installed")
print("\nRun:")
print("python test_oi_007_learning_ledger.py")