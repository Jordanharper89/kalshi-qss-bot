
"""
ORACLE-058 Expected Value Engine

Purpose:
- Estimate opportunity value after execution cost, fill probability,
  regime penalty, portfolio penalty, and execution gate penalty.
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


class OracleExpectedValueEngine:
    def __init__(self):
        self.version = "ORACLE-058"

    def analyze(self, item, market_regime=None):
        if not isinstance(item, dict):
            return self._result("error", "AVOID", 0, "Invalid opportunity", {})

        obi = item.get("order_book_intelligence") if isinstance(item.get("order_book_intelligence"), dict) else {}
        metrics = obi.get("metrics") if isinstance(obi.get("metrics"), dict) else {}

        raw_edge = _num(metrics.get("raw_edge") or item.get("edge"), 0)
        tradable_edge = _num(item.get("tradable_edge") or metrics.get("tradable_edge"), 0)
        execution_cost = _num(item.get("execution_cost") or metrics.get("execution_cost"), 0)
        fill_probability = _num(item.get("fill_probability") or metrics.get("fill_probability"), 0) / 100.0

        consensus_conf = _num(item.get("consensus_confidence"), 0) / 100.0
        adaptive_score = _num(item.get("adaptive_score") or item.get("overall_score"), 0) / 100.0
        flow_score = _num(item.get("flow_score"), 0) / 100.0
        micro_score = _num(item.get("microstructure_score"), 0) / 100.0
        portfolio_score = _num(item.get("portfolio_exposure_score"), 0) / 100.0

        execution = _txt(item.get("execution_decision"))
        grade = _txt(item.get("grade"))
        tradability = _txt(item.get("tradability"))
        order_book = _txt(item.get("order_book_rating"))
        lifecycle = _txt(item.get("lifecycle_state"))
        portfolio = _txt(item.get("portfolio_decision"))
        regime = _txt(market_regime or item.get("market_regime"))

        if not regime:
            regime = "UNKNOWN"

        gross_ev = tradable_edge * fill_probability

        confidence_multiplier = max(0.20, min(1.20, (consensus_conf * 0.55) + (adaptive_score * 0.25) + (flow_score * 0.20)))

        quality_multiplier = max(0.10, min(1.20, (micro_score * 0.45) + (portfolio_score * 0.25) + (fill_probability * 0.30)))

        penalties = []
        penalty = 0.0

        if execution == "BLOCK":
            penalty += 0.06
            penalties.append("Gatekeeper BLOCK penalty")
        elif execution == "REQUIRES_REVIEW":
            penalty += 0.015
            penalties.append("Requires review penalty")
        elif execution == "EXECUTE":
            penalty -= 0.01
            penalties.append("Execution-ready bonus")

        if grade == "PASS":
            penalty += 0.035
            penalties.append("PASS grade penalty")

        if tradability == "UNTRADABLE":
            penalty += 0.07
            penalties.append("Untradable penalty")
        elif tradability == "POOR":
            penalty += 0.04
            penalties.append("Poor tradability penalty")

        if order_book == "UNUSABLE":
            penalty += 0.045
            penalties.append("Unusable order book penalty")
        elif order_book == "WEAK":
            penalty += 0.025
            penalties.append("Weak order book penalty")

        if lifecycle in ("BLOCKED", "STALE"):
            penalty += 0.025
            penalties.append("Lifecycle blocked/stale penalty")

        if portfolio == "BLOCK_EXPOSURE":
            penalty += 0.045
            penalties.append("Portfolio exposure block penalty")
        elif portfolio == "REVIEW":
            penalty += 0.02
            penalties.append("Portfolio review penalty")

        if regime == "THIN_LIQUIDITY":
            penalty += 0.035
            penalties.append("Thin liquidity regime penalty")
        elif regime == "NOISY_ARBITRAGE":
            penalty += 0.025
            penalties.append("Noisy arbitrage regime penalty")
        elif regime == "RISK_OFF":
            penalty += 0.04
            penalties.append("Risk-off regime penalty")
        elif regime == "EXECUTION_FRIENDLY":
            penalty -= 0.015
            penalties.append("Execution-friendly regime bonus")
        elif regime == "TRENDING_EDGE":
            penalty -= 0.01
            penalties.append("Trending-edge regime bonus")

        adjusted_ev = (gross_ev * confidence_multiplier * quality_multiplier) - max(0.0, penalty)
        ev_score = max(0.0, min(100.0, adjusted_ev * 100.0))

        if ev_score >= 12 and execution in ("EXECUTE", "REQUIRES_REVIEW"):
            decision = "POSITIVE_EV"
        elif ev_score >= 6:
            decision = "WATCH_EV"
        elif ev_score >= 2:
            decision = "WEAK_EV"
        else:
            decision = "NEGATIVE_EV"

        reason = (
            f"EV {decision}. gross_ev={gross_ev:.4f}, adjusted_ev={adjusted_ev:.4f}, "
            f"fill={fill_probability:.2%}, tradable_edge={tradable_edge:.4f}, penalty={penalty:.4f}."
        )

        payload = {
            "raw_edge": round(raw_edge, 6),
            "tradable_edge": round(tradable_edge, 6),
            "execution_cost": round(execution_cost, 6),
            "fill_probability": round(fill_probability * 100, 2),
            "gross_ev": round(gross_ev, 6),
            "adjusted_ev": round(adjusted_ev, 6),
            "ev_score": round(ev_score, 2),
            "decision": decision,
            "confidence_multiplier": round(confidence_multiplier, 4),
            "quality_multiplier": round(quality_multiplier, 4),
            "penalty": round(penalty, 6),
            "penalties": penalties,
            "regime": regime,
        }

        return self._result("ok", decision, ev_score, reason, payload)

    def _result(self, status, decision, score, reason, payload):
        return {
            "module": "oracle_expected_value_engine",
            "version": self.version,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "ev_decision": decision,
            "ev_score": round(float(score or 0), 2),
            "reason": reason,
            "metrics": payload,
            "compact_card": self._card(decision, score, reason, payload),
        }

    def _card(self, decision, score, reason, payload):
        lines = [
            "💰 ORACLE EXPECTED VALUE",
            f"Decision: {decision}",
            f"EV Score: {round(float(score or 0), 2)}",
            "",
            f"Raw Edge: {payload.get('raw_edge')}",
            f"Tradable Edge: {payload.get('tradable_edge')}",
            f"Execution Cost: {payload.get('execution_cost')}",
            f"Fill Probability: {payload.get('fill_probability')}%",
            f"Gross EV: {payload.get('gross_ev')}",
            f"Adjusted EV: {payload.get('adjusted_ev')}",
            f"Regime: {payload.get('regime')}",
            "",
            f"Reason: {reason}",
        ]

        penalties = payload.get("penalties") or []
        if penalties:
            lines.append("")
            lines.append("Penalties / Bonuses:")
            for p in penalties[:8]:
                lines.append(f"- {p}")

        return "\n".join(lines)

    def diagnostics(self):
        return {
            "module": "oracle_expected_value_engine",
            "version": self.version,
            "status": "ok",
            "outputs": ["ev_decision", "ev_score", "ev_card"],
        }


oracle_expected_value_engine = OracleExpectedValueEngine()


if __name__ == "__main__":
    sample = {
        "ticker": "TEST",
        "edge": 0.20,
        "tradable_edge": 0.12,
        "execution_cost": 0.03,
        "fill_probability": 60,
        "consensus_confidence": 82,
        "adaptive_score": 75,
        "flow_score": 70,
        "microstructure_score": 68,
        "portfolio_exposure_score": 90,
        "execution_decision": "REQUIRES_REVIEW",
        "grade": "A-",
        "tradability": "CAUTION",
        "order_book_rating": "FAIR",
        "lifecycle_state": "IMPROVING",
        "portfolio_decision": "ALLOW",
    }

    import pprint
    pprint.pp(oracle_expected_value_engine.analyze(sample, "TRENDING_EDGE"))
