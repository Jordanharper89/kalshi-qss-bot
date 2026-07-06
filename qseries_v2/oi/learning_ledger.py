"""
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
