from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
TARGET = ROOT / "oracle_expected_value_engine.py"
CONTINUOUS = ROOT / "oracle_continuous_intelligence.py"

CODE = r'''
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
'''

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-058 Expected Value Engine Integration
# ============================================================

try:
    from oracle_expected_value_engine import oracle_expected_value_engine
except Exception:
    oracle_expected_value_engine = None


def _oracle058_apply_ev(ranked, market_regime=None):
    if oracle_expected_value_engine is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            ev = oracle_expected_value_engine.analyze(item, market_regime)
            item["expected_value"] = ev
            item["ev_decision"] = ev.get("ev_decision")
            item["ev_score"] = ev.get("ev_score")
            item["ev_metrics"] = ev.get("metrics", {})
            item["ev_card"] = ev.get("compact_card")
        except Exception as exc:
            item["expected_value"] = {
                "status": "error",
                "ev_decision": "NEGATIVE_EV",
                "reason": str(exc),
            }
            item["ev_decision"] = "NEGATIVE_EV"
            item["ev_score"] = 0

        enriched.append(item)

    ev_rank = {
        "POSITIVE_EV": 4,
        "WATCH_EV": 3,
        "WEAK_EV": 2,
        "NEGATIVE_EV": 1,
    }

    enriched.sort(
        key=lambda x: (
            ev_rank.get(x.get("ev_decision"), 0),
            x.get("ev_score", 0) or 0,
            x.get("queue_score", 0) or 0,
            x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0))),
        ) if isinstance(x, dict) else (0, 0, 0, 0),
        reverse=True,
    )

    return enriched


def _oracle058_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            regime = _state.get("market_regime")

            if isinstance(ranked, list):
                _state["last_ranked"] = _oracle058_apply_ev(ranked, regime)

                counts = {}
                for item in _state["last_ranked"]:
                    if isinstance(item, dict):
                        d = item.get("ev_decision", "UNKNOWN")
                        counts[d] = counts.get(d, 0) + 1

                _state["expected_value_status"] = {
                    "status": "ok" if oracle_expected_value_engine is not None else "missing",
                    "ev_counts": counts,
                    "top": _state["last_ranked"][:5],
                }
            else:
                _state["expected_value_status"] = {"status": "no_ranked_data"}
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["expected_value_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle058_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle058_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle058_original_run_cycle(*args, **kwargs)
        _oracle058_enrich_state()
        return result


if "_oracle058_original_status" not in globals() and "status" in globals():
    _oracle058_original_status = status

    def status(*args, **kwargs):
        result = _oracle058_original_status(*args, **kwargs)
        _oracle058_enrich_state()

        if isinstance(result, dict):
            result["expected_value_status"] = (
                globals().get("_state", {}).get("expected_value_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-058
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle058_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-058 INSTALLER")
    print(" Expected Value Engine")
    print("===================================")

    backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")
    print("[OK] Created oracle_expected_value_engine.py")

    if not CONTINUOUS.exists():
        print("[WARN] oracle_continuous_intelligence.py not found; integration skipped")
    else:
        text = CONTINUOUS.read_text(encoding="utf-8", errors="ignore")
        if "ORACLE-058 Expected Value Engine Integration" in text:
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

    print("")
    print("Tests:")
    print(" python oracle_expected_value_engine.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('expected_value_status')); print(s.get('last_ranked',[{}])[0].get('ev_card'))\"")
    print("")
    print("[DONE] ORACLE-058 Expected Value Engine installed")


if __name__ == "__main__":
    main()