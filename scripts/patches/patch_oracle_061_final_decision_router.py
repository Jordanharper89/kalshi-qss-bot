from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
TARGET = ROOT / "oracle_final_decision_router.py"
CONTINUOUS = ROOT / "oracle_continuous_intelligence.py"

CODE = r'''
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
'''

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-061 Final Decision Router Integration
# ============================================================

try:
    from oracle_final_decision_router import oracle_final_decision_router
except Exception:
    oracle_final_decision_router = None


def _oracle061_apply_final_decision(ranked, market_regime=None):
    if oracle_final_decision_router is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            fd = oracle_final_decision_router.route(item, market_regime)
            item["final_decision"] = fd
            item["oracle_final_action"] = fd.get("final_action")
            item["oracle_final_score"] = fd.get("final_score")
            item["oracle_final_card"] = fd.get("compact_card")
        except Exception as exc:
            item["final_decision"] = {
                "status": "error",
                "final_action": "NO_TRADE",
                "reason": str(exc),
            }
            item["oracle_final_action"] = "NO_TRADE"
            item["oracle_final_score"] = 0

        enriched.append(item)

    rank = {
        "READY_FOR_EXECUTION": 4,
        "HUMAN_REVIEW": 3,
        "WATCH": 2,
        "NO_TRADE": 1,
    }

    enriched.sort(
        key=lambda x: (
            rank.get(x.get("oracle_final_action"), 0),
            x.get("oracle_final_score", 0) or 0,
            x.get("trade_readiness_score", 0) or 0,
            x.get("ev_score", 0) or 0,
        ) if isinstance(x, dict) else (0, 0, 0, 0),
        reverse=True,
    )

    return enriched


def _oracle061_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            regime = _state.get("market_regime")

            if isinstance(ranked, list):
                _state["last_ranked"] = _oracle061_apply_final_decision(ranked, regime)

                counts = {}
                for item in _state["last_ranked"]:
                    if isinstance(item, dict):
                        a = item.get("oracle_final_action", "UNKNOWN")
                        counts[a] = counts.get(a, 0) + 1

                _state["final_decision_status"] = {
                    "status": "ok" if oracle_final_decision_router is not None else "missing",
                    "action_counts": counts,
                    "top": _state["last_ranked"][:5],
                }
            else:
                _state["final_decision_status"] = {"status": "no_ranked_data"}
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["final_decision_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle061_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle061_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle061_original_run_cycle(*args, **kwargs)
        _oracle061_enrich_state()
        return result


if "_oracle061_original_status" not in globals() and "status" in globals():
    _oracle061_original_status = status

    def status(*args, **kwargs):
        result = _oracle061_original_status(*args, **kwargs)
        _oracle061_enrich_state()

        if isinstance(result, dict):
            result["final_decision_status"] = (
                globals().get("_state", {}).get("final_decision_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-061
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle061_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-061 INSTALLER")
    print(" Final Decision Router")
    print("===================================")

    backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")
    print("[OK] Created oracle_final_decision_router.py")

    if not CONTINUOUS.exists():
        print("[WARN] oracle_continuous_intelligence.py not found; integration skipped")
    else:
        text = CONTINUOUS.read_text(encoding="utf-8", errors="ignore")
        if "ORACLE-061 Final Decision Router Integration" in text:
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
    print(" python oracle_final_decision_router.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('final_decision_status')); print(s.get('last_ranked',[{}])[0].get('oracle_final_card'))\"")
    print("")
    print("[DONE] ORACLE-061 Final Decision Router installed")


if __name__ == "__main__":
    main()