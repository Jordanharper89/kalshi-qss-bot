
"""
ORACLE-068 Signal Learning Memory

Purpose:
- Store outcome scores by signal pattern.
- Learn which regimes/categories/actions/EV states are performing.
- Does NOT place trades.
"""

from datetime import datetime, UTC
from pathlib import Path
import json

STATE_FILE = Path("oracle_signal_learning_memory_state.json")


def _num(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _txt(v):
    return str(v or "").strip().upper()


class OracleSignalLearningMemory:
    def __init__(self):
        self.version = "ORACLE-068"
        self.state = {
            "patterns": {},
            "history": [],
        }
        self._load()

    def learn(self, ranked, outcome_scores):
        ranked = ranked if isinstance(ranked, list) else []
        outcome_scores = outcome_scores if isinstance(outcome_scores, list) else []

        outcome_by_ticker = {}
        for o in outcome_scores:
            if isinstance(o, dict):
                outcome_by_ticker[o.get("ticker")] = o

        learned = []

        for item in ranked:
            if not isinstance(item, dict):
                continue

            outcome = outcome_by_ticker.get(item.get("ticker"))
            if not outcome:
                continue

            pattern_key = self._pattern_key(item)
            pattern = self.state["patterns"].setdefault(pattern_key, self._new_pattern(pattern_key, item))

            score = _num(outcome.get("outcome_score"), 50)
            pnl = _num(outcome.get("paper_pnl"), 0)

            pattern["samples"] += 1
            pattern["total_outcome_score"] += score
            pattern["avg_outcome_score"] = round(pattern["total_outcome_score"] / pattern["samples"], 2)
            pattern["total_paper_pnl"] += pnl
            pattern["avg_paper_pnl"] = round(pattern["total_paper_pnl"] / pattern["samples"], 6)

            if score >= 62:
                pattern["wins"] += 1
            elif score < 45:
                pattern["losses"] += 1
            else:
                pattern["neutral"] += 1

            pattern["win_rate"] = round(pattern["wins"] / pattern["samples"] * 100, 2)
            pattern["last_seen"] = datetime.now(UTC).isoformat()
            pattern["last_outcome"] = outcome

            learned.append(pattern)

        self.state["history"].append({
            "timestamp": datetime.now(UTC).isoformat(),
            "learned": len(learned),
            "patterns": len(self.state["patterns"]),
        })
        self.state["history"] = self.state["history"][-500:]

        self._save()

        return {
            "module": "oracle_signal_learning_memory",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "learned": len(learned),
            "patterns": len(self.state["patterns"]),
            "top_patterns": self.top_patterns(),
            "state_file": str(STATE_FILE),
        }

    def _pattern_key(self, item):
        parts = [
            _txt(item.get("market_regime")),
            _txt(item.get("oracle_final_action")),
            _txt(item.get("ev_decision")),
            _txt(item.get("trade_readiness_verdict")),
            _txt(item.get("tradability")),
            _txt(item.get("order_book_rating")),
            _txt(item.get("flow_signal")),
            _txt(item.get("portfolio_decision")),
        ]
        return "|".join(parts)

    def _new_pattern(self, key, item):
        return {
            "pattern_key": key,
            "created_at": datetime.now(UTC).isoformat(),
            "last_seen": datetime.now(UTC).isoformat(),
            "samples": 0,
            "wins": 0,
            "losses": 0,
            "neutral": 0,
            "win_rate": 0.0,
            "total_outcome_score": 0.0,
            "avg_outcome_score": 0.0,
            "total_paper_pnl": 0.0,
            "avg_paper_pnl": 0.0,
            "example": {
                "market_regime": item.get("market_regime"),
                "oracle_final_action": item.get("oracle_final_action"),
                "ev_decision": item.get("ev_decision"),
                "trade_readiness_verdict": item.get("trade_readiness_verdict"),
                "tradability": item.get("tradability"),
                "order_book_rating": item.get("order_book_rating"),
                "flow_signal": item.get("flow_signal"),
                "portfolio_decision": item.get("portfolio_decision"),
            },
        }

    def top_patterns(self, limit=10):
        rows = list(self.state.get("patterns", {}).values())
        rows.sort(
            key=lambda x: (
                x.get("avg_outcome_score", 0),
                x.get("win_rate", 0),
                x.get("samples", 0),
            ),
            reverse=True,
        )
        return rows[:limit]

    def diagnostics(self):
        return {
            "module": "oracle_signal_learning_memory",
            "version": self.version,
            "status": "ok",
            "patterns": len(self.state.get("patterns", {})),
            "state_file": str(STATE_FILE),
            "top_patterns": self.top_patterns(5),
        }

    def _load(self):
        try:
            if STATE_FILE.exists():
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.state.update(data)
        except Exception:
            pass

    def _save(self):
        try:
            STATE_FILE.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        except Exception:
            pass


oracle_signal_learning_memory = OracleSignalLearningMemory()


if __name__ == "__main__":
    sample_ranked = [{
        "ticker": "TEST",
        "market_regime": "TRENDING_EDGE",
        "oracle_final_action": "HUMAN_REVIEW",
        "ev_decision": "WATCH_EV",
        "trade_readiness_verdict": "REVIEW_READY",
        "tradability": "CAUTION",
        "order_book_rating": "FAIR",
        "flow_signal": "IMPROVING_FLOW",
        "portfolio_decision": "ALLOW",
    }]

    sample_outcomes = [{
        "ticker": "TEST",
        "outcome_score": 72,
        "paper_pnl": 0.03,
    }]

    import pprint
    pprint.pp(oracle_signal_learning_memory.learn(sample_ranked, sample_outcomes))
