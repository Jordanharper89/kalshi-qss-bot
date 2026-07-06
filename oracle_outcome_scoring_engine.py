
"""
ORACLE-067 Outcome Scoring Engine

Purpose:
- Score open tracked Oracle trades using paper P&L, MFE, MAE, and signal quality.
- Builds foundation for self-learning.
- Does NOT place trades.
"""

from datetime import datetime, UTC


def _num(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


class OracleOutcomeScoringEngine:
    def __init__(self):
        self.version = "ORACLE-067"

    def score_trades(self, trades):
        trades = trades if isinstance(trades, list) else []
        scored = []

        for trade in trades:
            if isinstance(trade, dict):
                scored.append(self.score_trade(trade))

        counts = {}
        for s in scored:
            outcome = s.get("outcome_grade", "UNKNOWN")
            counts[outcome] = counts.get(outcome, 0) + 1

        return {
            "module": "oracle_outcome_scoring_engine",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "scored": len(scored),
            "outcome_counts": counts,
            "scored_trades": scored,
        }

    def score_trade(self, trade):
        pnl = _num(trade.get("paper_pnl"), 0)
        mfe = _num(trade.get("mfe"), 0)
        mae = _num(trade.get("mae"), 0)
        updates = int(_num(trade.get("updates"), 0))

        final_score = _num(trade.get("oracle_final_score"), 0)
        ev_score = _num(trade.get("ev_score"), 0)

        score = 50.0
        notes = []

        if pnl > 0.05:
            score += 25
            notes.append("Paper P&L strongly positive")
        elif pnl > 0.02:
            score += 15
            notes.append("Paper P&L positive")
        elif pnl < -0.05:
            score -= 25
            notes.append("Paper P&L strongly negative")
        elif pnl < -0.02:
            score -= 15
            notes.append("Paper P&L negative")

        if mfe > 0.05:
            score += 12
            notes.append("Strong favorable excursion")
        elif mfe > 0.02:
            score += 6
            notes.append("Some favorable excursion")

        if mae < -0.05:
            score -= 12
            notes.append("Large adverse excursion")
        elif mae < -0.02:
            score -= 6
            notes.append("Some adverse excursion")

        if updates >= 3:
            score += 4
            notes.append("Multiple updates observed")

        if final_score >= 75 and pnl <= 0:
            score -= 8
            notes.append("High Oracle score has not produced positive paper P&L yet")

        if ev_score >= 8 and pnl > 0:
            score += 8
            notes.append("EV score aligned with positive outcome")

        score = max(0.0, min(100.0, score))

        if score >= 80:
            grade = "WINNING_SIGNAL"
        elif score >= 62:
            grade = "PROMISING_SIGNAL"
        elif score >= 45:
            grade = "NEUTRAL_SIGNAL"
        elif score >= 30:
            grade = "WEAK_SIGNAL"
        else:
            grade = "FAILING_SIGNAL"

        return {
            "module": "oracle_outcome_scoring_engine",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "trade_id": trade.get("trade_id"),
            "ticker": trade.get("ticker"),
            "title": trade.get("title"),
            "outcome_grade": grade,
            "outcome_score": round(score, 2),
            "paper_pnl": pnl,
            "mfe": mfe,
            "mae": mae,
            "updates": updates,
            "notes": notes,
            "compact_card": self._card(trade, grade, score, notes),
        }

    def _card(self, trade, grade, score, notes):
        lines = [
            "🧪 ORACLE OUTCOME SCORE",
            f"Trade ID: {trade.get('trade_id')}",
            f"Ticker: {trade.get('ticker')}",
            f"Market: {trade.get('title')}",
            "",
            f"Outcome Grade: {grade}",
            f"Outcome Score: {round(score, 2)}",
            f"Paper P&L: {trade.get('paper_pnl')}",
            f"MFE: {trade.get('mfe')}",
            f"MAE: {trade.get('mae')}",
            f"Updates: {trade.get('updates')}",
        ]

        if notes:
            lines.append("")
            lines.append("Notes:")
            for n in notes[:8]:
                lines.append(f"- {n}")

        return "\n".join(lines)

    def diagnostics(self):
        return {
            "module": "oracle_outcome_scoring_engine",
            "version": self.version,
            "status": "ok",
            "outputs": ["outcome_grade", "outcome_score", "outcome_card"],
        }


oracle_outcome_scoring_engine = OracleOutcomeScoringEngine()


if __name__ == "__main__":
    sample = [{
        "trade_id": "abc123",
        "ticker": "TEST",
        "title": "Sample outcome trade",
        "paper_pnl": 0.035,
        "mfe": 0.06,
        "mae": -0.01,
        "updates": 4,
        "oracle_final_score": 72,
        "ev_score": 8,
    }]

    import pprint
    pprint.pp(oracle_outcome_scoring_engine.score_trades(sample))
