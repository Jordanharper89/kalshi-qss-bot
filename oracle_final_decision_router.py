
"""
ORACLE-061 Final Decision Router

Purpose:
- Convert all Oracle subsystems into one final decision object.
- Future Q Series execution should read this layer only.
- Does NOT place trades.
"""

from datetime import datetime, UTC


def _txt(v):
    return str(v or "").strip().upper()


def _num(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


class OracleFinalDecisionRouter:
    def __init__(self):
        self.version = "ORACLE-061"

    def route(self, item, market_regime=None):
        if not isinstance(item, dict):
            return self._result("error", "NO_ACTION", 0, "Invalid opportunity", {})

        readiness = item.get("trade_readiness") if isinstance(item.get("trade_readiness"), dict) else {}
        ev = item.get("expected_value") if isinstance(item.get("expected_value"), dict) else {}
        queue = item.get("execution_queue") if isinstance(item.get("execution_queue"), dict) else {}

        verdict = _txt(item.get("trade_readiness_verdict") or readiness.get("verdict"))
        readiness_score = _num(item.get("trade_readiness_score") or readiness.get("readiness_score"), 0)

        ev_decision = _txt(item.get("ev_decision") or ev.get("ev_decision"))
        ev_score = _num(item.get("ev_score") or ev.get("ev_score"), 0)

        queue_decision = _txt(item.get("queue_decision") or queue.get("queue_decision"))
        queue_score = _num(item.get("queue_score") or queue.get("queue_score"), 0)

        execution_decision = _txt(item.get("execution_decision"))
        consensus = _txt(item.get("consensus_final_recommendation"))
        consensus_conf = _num(item.get("consensus_confidence"), 0)
        portfolio = _txt(item.get("portfolio_decision"))
        tradability = _txt(item.get("tradability"))
        order_book = _txt(item.get("order_book_rating"))
        grade = _txt(item.get("grade"))
        regime = _txt(market_regime or item.get("market_regime"))

        score = 0.0
        blockers = []
        supports = []
        notes = []

        if verdict == "READY":
            score += 40
            supports.append("Trade readiness verdict READY")
        elif verdict == "REVIEW_READY":
            score += 28
            supports.append("Trade readiness verdict REVIEW_READY")
        elif verdict == "WATCH_ONLY":
            score += 12
            notes.append("Trade readiness is WATCH_ONLY")
        elif verdict == "NOT_READY":
            score -= 35
            blockers.append("Trade readiness verdict NOT_READY")

        if ev_decision == "POSITIVE_EV":
            score += 25
            supports.append("Positive EV")
        elif ev_decision == "WATCH_EV":
            score += 10
            notes.append("Watch-level EV")
        elif ev_decision == "WEAK_EV":
            score -= 8
            notes.append("Weak EV")
        elif ev_decision == "NEGATIVE_EV":
            score -= 28
            blockers.append("Negative EV")

        if execution_decision == "EXECUTE":
            score += 30
            supports.append("Gatekeeper allows EXECUTE")
        elif execution_decision == "REQUIRES_REVIEW":
            score += 16
            notes.append("Gatekeeper requires review")
        elif execution_decision == "WATCH_ONLY":
            score += 8
            notes.append("Gatekeeper watch only")
        elif execution_decision == "BLOCK":
            score -= 35
            blockers.append("Gatekeeper blocks execution")

        if queue_decision == "EXECUTION_READY":
            score += 30
            supports.append("Execution queue says EXECUTION_READY")
        elif queue_decision == "REVIEW_REQUIRED":
            score += 18
            notes.append("Execution queue says REVIEW_REQUIRED")
        elif queue_decision == "WATCH_QUEUE":
            score += 8
            notes.append("Execution queue says WATCH_QUEUE")
        elif queue_decision == "REJECTED":
            score -= 25
            blockers.append("Execution queue rejected")

        if portfolio == "BLOCK_EXPOSURE":
            score -= 25
            blockers.append("Portfolio exposure blocks")
        elif portfolio == "ALLOW":
            score += 10
            supports.append("Portfolio exposure allows")

        if tradability in ("POOR", "UNTRADABLE"):
            score -= 20
            blockers.append(f"Tradability {tradability}")
        elif tradability in ("GOOD", "CAUTION"):
            score += 8
            supports.append(f"Tradability {tradability}")

        if order_book in ("WEAK", "UNUSABLE"):
            score -= 18
            blockers.append(f"Order book {order_book}")
        elif order_book in ("GOOD", "FAIR"):
            score += 8
            supports.append(f"Order book {order_book}")

        if grade == "PASS":
            score -= 18
            blockers.append("Grade PASS")

        if consensus in ("BUY YES", "BUY NO") and consensus_conf >= 70:
            score += 15
            supports.append("Directional consensus with acceptable confidence")
        elif consensus == "WATCH":
            notes.append("Consensus is WATCH")

        if regime in ("THIN_LIQUIDITY", "RISK_OFF", "NOISY_ARBITRAGE"):
            score -= 10
            notes.append(f"Market regime caution: {regime}")
        elif regime in ("EXECUTION_FRIENDLY", "TRENDING_EDGE"):
            score += 10
            supports.append(f"Market regime supportive: {regime}")

        score = max(0.0, min(100.0, score))

        if blockers:
            final_action = "NO_TRADE"
        elif score >= 85:
            final_action = "READY_FOR_EXECUTION"
        elif score >= 65:
            final_action = "HUMAN_REVIEW"
        elif score >= 40:
            final_action = "WATCH"
        else:
            final_action = "NO_TRADE"

        payload = {
            "ticker": item.get("ticker"),
            "title": item.get("title"),
            "side": item.get("side") or item.get("consensus_final_recommendation"),
            "final_action": final_action,
            "final_score": round(score, 2),
            "readiness_verdict": verdict,
            "readiness_score": readiness_score,
            "ev_decision": ev_decision,
            "ev_score": ev_score,
            "queue_decision": queue_decision,
            "queue_score": queue_score,
            "execution_decision": execution_decision,
            "consensus": consensus,
            "consensus_confidence": consensus_conf,
            "market_regime": regime,
            "blockers": blockers,
            "supports": supports,
            "notes": notes,
        }

        reason = f"Final action {final_action} with score {score:.2f}."

        return self._result("ok", final_action, score, reason, payload)

    def _result(self, status, action, score, reason, payload):
        return {
            "module": "oracle_final_decision_router",
            "version": self.version,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "final_action": action,
            "final_score": round(float(score or 0), 2),
            "reason": reason,
            **payload,
            "compact_card": self._card(payload, reason),
        }

    def _card(self, p, reason):
        lines = [
            "🧠 ORACLE FINAL DECISION",
            f"Ticker: {p.get('ticker')}",
            f"Market: {p.get('title')}",
            "",
            f"Final Action: {p.get('final_action')}",
            f"Final Score: {p.get('final_score')}",
            f"Side: {p.get('side')}",
            "",
            f"Readiness: {p.get('readiness_verdict')} | {p.get('readiness_score')}",
            f"EV: {p.get('ev_decision')} | {p.get('ev_score')}",
            f"Queue: {p.get('queue_decision')} | {p.get('queue_score')}",
            f"Gatekeeper: {p.get('execution_decision')}",
            f"Consensus: {p.get('consensus')} | {p.get('consensus_confidence')}%",
            f"Regime: {p.get('market_regime')}",
            "",
            f"Reason: {reason}",
        ]

        if p.get("blockers"):
            lines.append("")
            lines.append("Blockers:")
            for b in p["blockers"][:8]:
                lines.append(f"- {b}")

        if p.get("supports"):
            lines.append("")
            lines.append("Supports:")
            for s in p["supports"][:8]:
                lines.append(f"- {s}")

        if p.get("notes"):
            lines.append("")
            lines.append("Notes:")
            for n in p["notes"][:8]:
                lines.append(f"- {n}")

        return "\n".join(lines)

    def diagnostics(self):
        return {
            "module": "oracle_final_decision_router",
            "version": self.version,
            "status": "ok",
            "actions": ["READY_FOR_EXECUTION", "HUMAN_REVIEW", "WATCH", "NO_TRADE"],
        }


oracle_final_decision_router = OracleFinalDecisionRouter()




# ============================================================
# ORACLE-070 Learning-Aware Final Router Overlay
# ============================================================

if "OracleFinalDecisionRouter" in globals():
    if "_oracle070_original_route" not in globals():
        _oracle070_original_route = OracleFinalDecisionRouter.route

        def _oracle070_route(self, item, market_regime=None):
            base = _oracle070_original_route(self, item, market_regime)

            if not isinstance(base, dict) or not isinstance(item, dict):
                return base

            learning = item.get("learning_adapter") if isinstance(item.get("learning_adapter"), dict) else {}

            adjusted_score = float(
                item.get("learning_adjusted_score")
                or learning.get("adjusted_score")
                or base.get("final_score")
                or 0
            )

            learning_conf = str(
                item.get("learning_confidence")
                or learning.get("learning_confidence")
                or "NONE"
            ).upper()

            boost = float(item.get("learning_boost") or learning.get("learning_boost") or 0)
            penalty = float(item.get("learning_penalty") or learning.get("learning_penalty") or 0)

            original_action = base.get("final_action", "NO_TRADE")
            final_action = original_action
            notes = list(base.get("notes", []))
            blockers = list(base.get("blockers", []))
            supports = list(base.get("supports", []))

            if learning_conf in ("HIGH", "MEDIUM"):
                if penalty >= 8 and original_action in ("READY_FOR_EXECUTION", "HUMAN_REVIEW"):
                    final_action = "HUMAN_REVIEW" if original_action == "READY_FOR_EXECUTION" else "WATCH"
                    blockers.append("Learning memory downgraded this pattern")

                elif boost >= 8 and original_action == "WATCH" and adjusted_score >= 65:
                    final_action = "HUMAN_REVIEW"
                    supports.append("Learning memory upgraded WATCH to HUMAN_REVIEW")

                elif boost >= 8 and original_action == "HUMAN_REVIEW" and adjusted_score >= 85:
                    final_action = "READY_FOR_EXECUTION"
                    supports.append("Learning memory supports execution-ready upgrade")
            else:
                notes.append("Learning memory sample size not strong enough for major decision change")

            base["pre_learning_final_action"] = original_action
            base["final_action"] = final_action
            base["oracle_final_action"] = final_action
            base["final_score"] = round(adjusted_score, 2)
            base["oracle_final_score"] = round(adjusted_score, 2)
            base["notes"] = notes
            base["blockers"] = blockers
            base["supports"] = supports
            base["learning_router_overlay"] = {
                "version": "ORACLE-070",
                "status": "applied",
                "learning_confidence": learning_conf,
                "learning_boost": boost,
                "learning_penalty": penalty,
                "original_action": original_action,
                "final_action": final_action,
                "adjusted_score": round(adjusted_score, 2),
            }

            base["compact_card"] = self._card(base, base.get("reason", ""))

            return base

        OracleFinalDecisionRouter.route = _oracle070_route

# ============================================================
# END ORACLE-070
# ============================================================


if __name__ == "__main__":
    sample = {
        "ticker": "TEST",
        "title": "Sample final decision",
        "side": "BUY YES",
        "grade": "A-",
        "consensus_final_recommendation": "BUY YES",
        "consensus_confidence": 82,
        "execution_decision": "REQUIRES_REVIEW",
        "portfolio_decision": "ALLOW",
        "tradability": "CAUTION",
        "order_book_rating": "FAIR",
        "trade_readiness_verdict": "REVIEW_READY",
        "trade_readiness_score": 72,
        "ev_decision": "WATCH_EV",
        "ev_score": 8,
        "queue_decision": "REVIEW_REQUIRED",
        "queue_score": 80,
    }

    import pprint
    pprint.pp(oracle_final_decision_router.route(sample, "TRENDING_EDGE"))
