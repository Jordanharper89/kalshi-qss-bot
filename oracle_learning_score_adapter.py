
"""
ORACLE-069 Learning Score Adapter

Purpose:
- Feed Signal Learning Memory back into live opportunities.
- Adds learning_boost, learning_penalty, adjusted_final_score.
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


def _txt(v):
    return str(v or "").strip().upper()


class OracleLearningScoreAdapter:
    def __init__(self):
        self.version = "ORACLE-069"

    def apply(self, ranked, patterns):
        ranked = ranked if isinstance(ranked, list) else []
        patterns = patterns if isinstance(patterns, list) else []

        pattern_map = {p.get("pattern_key"): p for p in patterns if isinstance(p, dict)}

        enriched = []

        for item in ranked:
            if not isinstance(item, dict):
                enriched.append(item)
                continue

            key = self._pattern_key(item)
            pattern = pattern_map.get(key)

            adapter = self._score_pattern(item, pattern)

            item["learning_adapter"] = adapter
            item["learning_pattern_key"] = key
            item["learning_boost"] = adapter.get("learning_boost")
            item["learning_penalty"] = adapter.get("learning_penalty")
            item["learning_adjusted_score"] = adapter.get("adjusted_score")
            item["learning_confidence"] = adapter.get("learning_confidence")
            item["learning_card"] = adapter.get("compact_card")

            enriched.append(item)

        enriched.sort(
            key=lambda x: (
                x.get("learning_adjusted_score", 0) or 0,
                x.get("oracle_final_score", 0) or 0,
                x.get("ev_score", 0) or 0,
            ) if isinstance(x, dict) else (0, 0, 0),
            reverse=True,
        )

        return {
            "module": "oracle_learning_score_adapter",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "count": len(enriched),
            "matched_patterns": sum(1 for x in enriched if isinstance(x, dict) and x.get("learning_adapter", {}).get("matched")),
            "top": enriched[:10],
            "ranked": enriched,
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

    def _score_pattern(self, item, pattern):
        base_score = _num(item.get("oracle_final_score"), 0)
        boost = 0.0
        penalty = 0.0
        confidence = "NONE"
        notes = []

        if not isinstance(pattern, dict):
            adjusted = base_score
            return self._result(False, base_score, adjusted, boost, penalty, confidence, notes, None)

        samples = int(_num(pattern.get("samples"), 0))
        win_rate = _num(pattern.get("win_rate"), 0)
        avg_outcome = _num(pattern.get("avg_outcome_score"), 50)
        avg_pnl = _num(pattern.get("avg_paper_pnl"), 0)

        if samples >= 20:
            confidence = "HIGH"
        elif samples >= 8:
            confidence = "MEDIUM"
        elif samples >= 3:
            confidence = "LOW"
        else:
            confidence = "VERY_LOW"

        if samples >= 3:
            if avg_outcome >= 70 and win_rate >= 60:
                boost += 8
                notes.append("Pattern has strong historical outcome score")
            elif avg_outcome >= 62:
                boost += 4
                notes.append("Pattern has promising historical outcome score")

            if avg_outcome < 45:
                penalty += 8
                notes.append("Pattern has weak historical outcome score")

            if win_rate < 35:
                penalty += 6
                notes.append("Pattern win rate is weak")

            if avg_pnl > 0.02:
                boost += 4
                notes.append("Pattern average paper P&L is positive")
            elif avg_pnl < -0.02:
                penalty += 4
                notes.append("Pattern average paper P&L is negative")
        else:
            notes.append("Pattern has limited sample size")

        adjusted = max(0.0, min(100.0, base_score + boost - penalty))

        return self._result(True, base_score, adjusted, boost, penalty, confidence, notes, pattern)

    def _result(self, matched, base_score, adjusted, boost, penalty, confidence, notes, pattern):
        return {
            "module": "oracle_learning_score_adapter",
            "version": self.version,
            "status": "ok",
            "matched": matched,
            "base_score": round(base_score, 2),
            "adjusted_score": round(adjusted, 2),
            "learning_boost": round(boost, 2),
            "learning_penalty": round(penalty, 2),
            "learning_confidence": confidence,
            "pattern_samples": pattern.get("samples") if isinstance(pattern, dict) else 0,
            "pattern_win_rate": pattern.get("win_rate") if isinstance(pattern, dict) else 0,
            "pattern_avg_outcome_score": pattern.get("avg_outcome_score") if isinstance(pattern, dict) else 0,
            "pattern_avg_paper_pnl": pattern.get("avg_paper_pnl") if isinstance(pattern, dict) else 0,
            "notes": notes,
            "compact_card": self._card(matched, base_score, adjusted, boost, penalty, confidence, notes, pattern),
        }

    def _card(self, matched, base, adjusted, boost, penalty, confidence, notes, pattern):
        lines = [
            "🧠 ORACLE LEARNING ADAPTER",
            f"Matched Pattern: {matched}",
            f"Learning Confidence: {confidence}",
            f"Base Score: {round(base, 2)}",
            f"Boost: {round(boost, 2)}",
            f"Penalty: {round(penalty, 2)}",
            f"Adjusted Score: {round(adjusted, 2)}",
        ]

        if isinstance(pattern, dict):
            lines.extend([
                "",
                f"Samples: {pattern.get('samples')}",
                f"Win Rate: {pattern.get('win_rate')}%",
                f"Avg Outcome: {pattern.get('avg_outcome_score')}",
                f"Avg Paper P&L: {pattern.get('avg_paper_pnl')}",
            ])

        if notes:
            lines.append("")
            lines.append("Notes:")
            for n in notes[:8]:
                lines.append(f"- {n}")

        return "\n".join(lines)

    def diagnostics(self):
        return {
            "module": "oracle_learning_score_adapter",
            "version": self.version,
            "status": "ok",
            "outputs": ["learning_boost", "learning_penalty", "learning_adjusted_score"],
        }


oracle_learning_score_adapter = OracleLearningScoreAdapter()


if __name__ == "__main__":
    sample_ranked = [{
        "ticker": "TEST",
        "oracle_final_score": 70,
        "market_regime": "TRENDING_EDGE",
        "oracle_final_action": "HUMAN_REVIEW",
        "ev_decision": "WATCH_EV",
        "trade_readiness_verdict": "REVIEW_READY",
        "tradability": "CAUTION",
        "order_book_rating": "FAIR",
        "flow_signal": "IMPROVING_FLOW",
        "portfolio_decision": "ALLOW",
    }]

    sample_patterns = [{
        "pattern_key": "TRENDING_EDGE|HUMAN_REVIEW|WATCH_EV|REVIEW_READY|CAUTION|FAIR|IMPROVING_FLOW|ALLOW",
        "samples": 5,
        "win_rate": 80,
        "avg_outcome_score": 72,
        "avg_paper_pnl": 0.03,
    }]

    import pprint
    pprint.pp(oracle_learning_score_adapter.apply(sample_ranked, sample_patterns))
