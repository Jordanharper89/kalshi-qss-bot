
"""
ORACLE-057 Market Regime Engine

Purpose:
- Classify Oracle's current opportunity environment.
- Regimes: QUIET, THIN_LIQUIDITY, NOISY_ARBITRAGE, TRENDING_EDGE,
  RISK_OFF, EXECUTION_FRIENDLY.
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


class OracleMarketRegimeEngine:
    def __init__(self):
        self.version = "ORACLE-057"

    def analyze(self, ranked):
        ranked = ranked if isinstance(ranked, list) else []

        total = len(ranked)
        if total == 0:
            return self._result("QUIET", 50, "No ranked opportunities available.", {}, [])

        stats = {
            "total": total,
            "execute": 0,
            "watch": 0,
            "blocked": 0,
            "pass_grade": 0,
            "poor_tradability": 0,
            "unusable_order_book": 0,
            "positive_flow": 0,
            "negative_flow": 0,
            "high_quality_price": 0,
            "low_quality_price": 0,
            "portfolio_blocked": 0,
            "avg_consensus_confidence": 0.0,
            "avg_adaptive_score": 0.0,
            "avg_tradable_edge": 0.0,
            "avg_fill_probability": 0.0,
        }

        confs = []
        scores = []
        tradable_edges = []
        fills = []

        categories = {}

        for item in ranked:
            if not isinstance(item, dict):
                continue

            execution = _txt(item.get("execution_decision"))
            grade = _txt(item.get("grade"))
            tradability = _txt(item.get("tradability"))
            order_book = _txt(item.get("order_book_rating"))
            flow = _txt(item.get("flow_signal"))
            price_quality = _txt(item.get("price_quality"))
            portfolio = _txt(item.get("portfolio_decision"))

            if execution == "EXECUTE":
                stats["execute"] += 1
            elif execution in ("WATCH_ONLY", "REQUIRES_REVIEW"):
                stats["watch"] += 1
            elif execution == "BLOCK":
                stats["blocked"] += 1

            if grade == "PASS":
                stats["pass_grade"] += 1

            if tradability in ("POOR", "UNTRADABLE"):
                stats["poor_tradability"] += 1

            if order_book in ("WEAK", "UNUSABLE"):
                stats["unusable_order_book"] += 1

            if flow in ("BULLISH_FLOW", "IMPROVING_FLOW"):
                stats["positive_flow"] += 1
            elif flow in ("DETERIORATING_FLOW", "AVOID_FLOW"):
                stats["negative_flow"] += 1

            if price_quality in ("HIGH", "MEDIUM"):
                stats["high_quality_price"] += 1
            elif price_quality in ("LOW", "VERY_LOW"):
                stats["low_quality_price"] += 1

            if portfolio == "BLOCK_EXPOSURE":
                stats["portfolio_blocked"] += 1

            confs.append(_num(item.get("consensus_confidence"), 0))
            scores.append(_num(item.get("adaptive_score") or item.get("overall_score"), 0))
            tradable_edges.append(_num(item.get("tradable_edge"), 0))
            fills.append(_num(item.get("fill_probability"), 0))

            category = "UNKNOWN"
            pe = item.get("portfolio_exposure")
            if isinstance(pe, dict):
                profile = pe.get("profile")
                if isinstance(profile, dict):
                    category = profile.get("category") or "UNKNOWN"
            categories[category] = categories.get(category, 0) + 1

        stats["avg_consensus_confidence"] = round(sum(confs) / len(confs), 2) if confs else 0
        stats["avg_adaptive_score"] = round(sum(scores) / len(scores), 2) if scores else 0
        stats["avg_tradable_edge"] = round(sum(tradable_edges) / len(tradable_edges), 6) if tradable_edges else 0
        stats["avg_fill_probability"] = round(sum(fills) / len(fills), 2) if fills else 0
        stats["categories"] = categories

        ratios = {
            "blocked_ratio": stats["blocked"] / total,
            "pass_ratio": stats["pass_grade"] / total,
            "poor_tradability_ratio": stats["poor_tradability"] / total,
            "unusable_order_book_ratio": stats["unusable_order_book"] / total,
            "positive_flow_ratio": stats["positive_flow"] / total,
            "negative_flow_ratio": stats["negative_flow"] / total,
            "portfolio_block_ratio": stats["portfolio_blocked"] / total,
        }

        regime, score, reason, actions = self._classify(stats, ratios)

        return self._result(regime, score, reason, stats, actions, ratios)

    def _classify(self, stats, ratios):
        actions = []

        if (
            ratios["poor_tradability_ratio"] >= 0.60
            or ratios["unusable_order_book_ratio"] >= 0.60
            or stats["avg_fill_probability"] < 35
        ):
            regime = "THIN_LIQUIDITY"
            score = 35
            reason = "Most opportunities have poor tradability, weak order books, or low fill probability."
            actions = [
                "Tighten execution queue.",
                "Prefer WATCH only.",
                "Require stronger fill probability before execution.",
            ]

        elif ratios["portfolio_block_ratio"] >= 0.50:
            regime = "NOISY_ARBITRAGE"
            score = 40
            reason = "Portfolio concentration is high; many opportunities are clustered in the same theme."
            actions = [
                "Suppress duplicate arbitrage alerts.",
                "Rank only the best opportunity per event family.",
                "Avoid overloading one theme.",
            ]

        elif ratios["negative_flow_ratio"] >= 0.50:
            regime = "RISK_OFF"
            score = 38
            reason = "Order flow is deteriorating across many opportunities."
            actions = [
                "Avoid new entries.",
                "Prioritize review and monitoring.",
                "Wait for flow recovery.",
            ]

        elif (
            ratios["positive_flow_ratio"] >= 0.45
            and stats["avg_tradable_edge"] > 0.05
            and stats["avg_consensus_confidence"] >= 65
        ):
            regime = "TRENDING_EDGE"
            score = 75
            reason = "Multiple opportunities show positive flow with meaningful tradable edge."
            actions = [
                "Allow review queue expansion.",
                "Prioritize improving lifecycle states.",
                "Watch for execution-ready upgrades.",
            ]

        elif (
            stats["execute"] > 0
            or (
                stats["avg_fill_probability"] >= 55
                and stats["avg_adaptive_score"] >= 65
                and ratios["poor_tradability_ratio"] < 0.35
            )
        ):
            regime = "EXECUTION_FRIENDLY"
            score = 85
            reason = "Market conditions are comparatively favorable for staged execution review."
            actions = [
                "Allow execution queue candidates.",
                "Respect portfolio limits.",
                "Require final gatekeeper approval.",
            ]

        else:
            regime = "QUIET"
            score = 55
            reason = "No strong execution regime detected."
            actions = [
                "Continue monitoring.",
                "Avoid forcing trades.",
                "Wait for stronger consensus or liquidity.",
            ]

        return regime, score, reason, actions

    def _result(self, regime, score, reason, stats, actions, ratios=None):
        return {
            "module": "oracle_market_regime_engine",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "regime": regime,
            "regime_score": score,
            "reason": reason,
            "stats": stats,
            "ratios": ratios or {},
            "recommended_actions": actions,
            "compact_card": self._card(regime, score, reason, stats, actions),
        }

    def _card(self, regime, score, reason, stats, actions):
        lines = [
            "🌐 ORACLE MARKET REGIME",
            f"Regime: {regime}",
            f"Score: {score}",
            "",
            f"Reason: {reason}",
            "",
            f"Total Opportunities: {stats.get('total')}",
            f"Blocked: {stats.get('blocked')}",
            f"PASS Grade: {stats.get('pass_grade')}",
            f"Poor Tradability: {stats.get('poor_tradability')}",
            f"Weak/Unusable Order Book: {stats.get('unusable_order_book')}",
            f"Positive Flow: {stats.get('positive_flow')}",
            f"Negative Flow: {stats.get('negative_flow')}",
            f"Avg Confidence: {stats.get('avg_consensus_confidence')}",
            f"Avg Fill Probability: {stats.get('avg_fill_probability')}",
            "",
            "Recommended Actions:",
        ]

        for a in actions:
            lines.append(f"- {a}")

        return "\n".join(lines)

    def diagnostics(self):
        return {
            "module": "oracle_market_regime_engine",
            "version": self.version,
            "status": "ok",
            "regimes": [
                "QUIET",
                "THIN_LIQUIDITY",
                "NOISY_ARBITRAGE",
                "TRENDING_EDGE",
                "RISK_OFF",
                "EXECUTION_FRIENDLY",
            ],
        }


oracle_market_regime_engine = OracleMarketRegimeEngine()


if __name__ == "__main__":
    sample = [
        {
            "ticker": "TEST",
            "grade": "PASS",
            "execution_decision": "BLOCK",
            "tradability": "POOR",
            "order_book_rating": "UNUSABLE",
            "flow_signal": "AVOID_FLOW",
            "consensus_confidence": 52,
            "adaptive_score": 51,
            "tradable_edge": 0.08,
            "fill_probability": 30,
            "portfolio_decision": "BLOCK_EXPOSURE",
        }
    ]

    import pprint
    pprint.pp(oracle_market_regime_engine.analyze(sample))
