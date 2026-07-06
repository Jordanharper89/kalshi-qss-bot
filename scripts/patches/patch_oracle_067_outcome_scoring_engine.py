from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
TARGET = ROOT / "oracle_outcome_scoring_engine.py"
CONTINUOUS = ROOT / "oracle_continuous_intelligence.py"

CODE = r'''
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
'''

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-067 Outcome Scoring Engine Integration
# ============================================================

try:
    from oracle_outcome_scoring_engine import oracle_outcome_scoring_engine
except Exception:
    oracle_outcome_scoring_engine = None


def _oracle067_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            trades = _state.get("live_trades", [])

            if oracle_outcome_scoring_engine is None:
                _state["outcome_scoring_status"] = {"status": "missing"}
                _state["outcome_scores"] = []
                return

            result = oracle_outcome_scoring_engine.score_trades(trades if isinstance(trades, list) else [])
            _state["outcome_scoring_status"] = result
            _state["outcome_scores"] = result.get("scored_trades", [])
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["outcome_scoring_status"] = {"status": "error", "error": str(exc)}
            _state["outcome_scores"] = []


if "_oracle067_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle067_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle067_original_run_cycle(*args, **kwargs)
        _oracle067_enrich_state()
        return result


if "_oracle067_original_status" not in globals() and "status" in globals():
    _oracle067_original_status = status

    def status(*args, **kwargs):
        result = _oracle067_original_status(*args, **kwargs)
        _oracle067_enrich_state()

        if isinstance(result, dict):
            result["outcome_scoring_status"] = (
                globals().get("_state", {}).get("outcome_scoring_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["outcome_scores"] = (
                globals().get("_state", {}).get("outcome_scores")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-067
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle067_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-067 INSTALLER")
    print(" Outcome Scoring Engine")
    print("===================================")

    backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")
    print("[OK] Created oracle_outcome_scoring_engine.py")

    if CONTINUOUS.exists():
        text = CONTINUOUS.read_text(encoding="utf-8", errors="ignore")
        if "ORACLE-067 Outcome Scoring Engine Integration" in text:
            print("[SKIP] Continuous Intelligence already patched")
        else:
            b = backup(CONTINUOUS)
            marker = 'if __name__ == "__main__":'
            if marker in text:
                text = text.replace(marker, PATCH_BLOCK + "\n\n" + marker, 1)
            else:
                text += "\n\n" + PATCH_BLOCK + "\n"
            CONTINUOUS.write_text(text, encoding="utf-8")
            print("[OK] Patched oracle_continuous_intelligence.py")
            print(f"[OK] Backup created: {b}")
    else:
        print("[WARN] oracle_continuous_intelligence.py not found")

    print("")
    print("Tests:")
    print(" python oracle_outcome_scoring_engine.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('outcome_scoring_status')); print(s.get('outcome_scores')[:3])\"")
    print("")
    print("[DONE] ORACLE-067 Outcome Scoring Engine installed")


if __name__ == "__main__":
    main()