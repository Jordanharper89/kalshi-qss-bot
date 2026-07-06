from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
TARGET = ROOT / "oracle_trade_readiness_report.py"
CONTINUOUS = ROOT / "oracle_continuous_intelligence.py"

CODE = r'''
"""
ORACLE-060 Trade Readiness Report

Purpose:
- Build one final institutional-style report per opportunity.
- Summarizes consensus, gatekeeper, EV, market regime, queue, portfolio,
  microstructure, order book, order flow, alerts, and lifecycle.
- Does NOT execute trades.
"""

from datetime import datetime, UTC


def _txt(v):
    return str(v or "").strip()


def _num(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


class OracleTradeReadinessReport:
    def __init__(self):
        self.version = "ORACLE-060"

    def build(self, item, market_regime=None):
        if not isinstance(item, dict):
            return self._result("error", "INVALID", 0, "Invalid opportunity", {})

        metrics = self._metrics(item, market_regime)
        score, verdict, blockers, supports, cautions = self._score(metrics)

        reason = (
            f"Trade readiness verdict {verdict}. "
            f"Score={score:.2f}. "
            f"Blockers={len(blockers)}, cautions={len(cautions)}, supports={len(supports)}."
        )

        payload = {
            "ticker": metrics["ticker"],
            "title": metrics["title"],
            "verdict": verdict,
            "readiness_score": round(score, 2),
            "reason": reason,
            "metrics": metrics,
            "blockers": blockers,
            "supports": supports,
            "cautions": cautions,
        }

        return self._result("ok", verdict, score, reason, payload)

    def _metrics(self, item, market_regime):
        ev = item.get("expected_value") if isinstance(item.get("expected_value"), dict) else {}
        ev_metrics = ev.get("metrics") if isinstance(ev.get("metrics"), dict) else {}

        queue = item.get("execution_queue") if isinstance(item.get("execution_queue"), dict) else {}
        portfolio = item.get("portfolio_exposure") if isinstance(item.get("portfolio_exposure"), dict) else {}
        pe_profile = portfolio.get("profile") if isinstance(portfolio.get("profile"), dict) else {}

        return {
            "ticker": item.get("ticker"),
            "title": item.get("title"),
            "side": _txt(item.get("side") or item.get("consensus_final_recommendation") or "WATCH"),
            "grade": _txt(item.get("grade")),
            "risk": _txt(item.get("risk")),
            "consensus": _txt(item.get("consensus_final_recommendation")),
            "consensus_confidence": _num(item.get("consensus_confidence"), 0),
            "consensus_strength": _txt(item.get("consensus_strength")),
            "execution_decision": _txt(item.get("execution_decision")),
            "policy_profile": _txt(
                item.get("execution_gate", {}).get("policy_profile")
                if isinstance(item.get("execution_gate"), dict)
                else ""
            ),
            "tradability": _txt(item.get("tradability")),
            "microstructure_score": _num(item.get("microstructure_score"), 0),
            "order_book_rating": _txt(item.get("order_book_rating")),
            "order_book_score": _num(item.get("order_book_score"), 0),
            "fill_probability": _num(item.get("fill_probability"), 0),
            "tradable_edge": _num(item.get("tradable_edge"), 0),
            "flow_signal": _txt(item.get("flow_signal")),
            "flow_score": _num(item.get("flow_score"), 0),
            "lifecycle_state": _txt(item.get("lifecycle_state")),
            "lifecycle_score": _num(item.get("lifecycle_score"), 0),
            "portfolio_decision": _txt(item.get("portfolio_decision") or portfolio.get("decision")),
            "portfolio_score": _num(item.get("portfolio_exposure_score") or portfolio.get("score"), 0),
            "portfolio_category": _txt(pe_profile.get("category")),
            "portfolio_event_family": _txt(pe_profile.get("event_family")),
            "price_quality": _txt(item.get("price_quality")),
            "price_quality_score": _num(item.get("price_quality_score"), 0),
            "ev_decision": _txt(item.get("ev_decision")),
            "ev_score": _num(item.get("ev_score"), 0),
            "adjusted_ev": _num(ev_metrics.get("adjusted_ev"), 0),
            "gross_ev": _num(ev_metrics.get("gross_ev"), 0),
            "oracle_final_action": _txt(item.get("oracle_final_action")),
            "queue_decision": _txt(item.get("queue_decision")),
            "queue_score": _num(item.get("queue_score"), 0),
            "market_regime": _txt(market_regime or item.get("market_regime")),
        }

    def _score(self, m):
        score = 50.0
        blockers = []
        supports = []
        cautions = []

        if m["execution_decision"] == "EXECUTE":
            score += 25
            supports.append("Gatekeeper marks EXECUTE")
        elif m["execution_decision"] == "WATCH_ONLY":
            score += 5
            cautions.append("Gatekeeper allows watch only")
        elif m["execution_decision"] == "BLOCK":
            score -= 35
            blockers.append("Gatekeeper blocks execution")

        if m["ev_decision"] == "POSITIVE_EV":
            score += 25
            supports.append("Expected Value is positive")
        elif m["ev_decision"] == "WATCH_EV":
            score += 8
            cautions.append("Expected Value supports watch only")
        elif m["ev_decision"] == "WEAK_EV":
            score -= 8
            cautions.append("Expected Value is weak")
        elif m["ev_decision"] == "NEGATIVE_EV":
            score -= 30
            blockers.append("Expected Value is negative")

        if m["portfolio_decision"] == "ALLOW":
            score += 12
            supports.append("Portfolio exposure allows")
        elif m["portfolio_decision"] == "LIMIT_SIZE":
            score += 2
            cautions.append("Portfolio requires limited size")
        elif m["portfolio_decision"] == "BLOCK_EXPOSURE":
            score -= 25
            blockers.append("Portfolio exposure blocks")

        if m["tradability"] == "GOOD":
            score += 15
            supports.append("Good tradability")
        elif m["tradability"] == "CAUTION":
            score += 4
            cautions.append("Tradability caution")
        elif m["tradability"] in ("POOR", "UNTRADABLE"):
            score -= 22
            blockers.append(f"Tradability is {m['tradability']}")

        if m["order_book_rating"] == "GOOD":
            score += 12
            supports.append("Good order book")
        elif m["order_book_rating"] == "FAIR":
            score += 4
            cautions.append("Order book fair")
        elif m["order_book_rating"] in ("WEAK", "UNUSABLE"):
            score -= 18
            blockers.append(f"Order book is {m['order_book_rating']}")

        if m["fill_probability"] >= 65:
            score += 8
            supports.append("Fill probability acceptable")
        elif m["fill_probability"] < 35:
            score -= 10
            cautions.append("Fill probability weak")

        if m["consensus_confidence"] >= 80:
            score += 12
            supports.append("High consensus confidence")
        elif m["consensus_confidence"] < 55:
            score -= 8
            cautions.append("Low consensus confidence")

        if m["grade"] == "PASS":
            score -= 15
            blockers.append("Opportunity grade is PASS")

        if m["flow_signal"] in ("BULLISH_FLOW", "IMPROVING_FLOW"):
            score += 8
            supports.append(f"Positive order flow: {m['flow_signal']}")
        elif m["flow_signal"] in ("DETERIORATING_FLOW", "AVOID_FLOW"):
            score -= 10
            cautions.append(f"Weak order flow: {m['flow_signal']}")

        if m["market_regime"] == "EXECUTION_FRIENDLY":
            score += 10
            supports.append("Market regime is execution-friendly")
        elif m["market_regime"] == "TRENDING_EDGE":
            score += 6
            supports.append("Market regime is trending edge")
        elif m["market_regime"] in ("THIN_LIQUIDITY", "RISK_OFF", "NOISY_ARBITRAGE"):
            score -= 10
            cautions.append(f"Market regime: {m['market_regime']}")

        score = max(0.0, min(100.0, score))

        if blockers:
            verdict = "NOT_READY"
        elif score >= 85:
            verdict = "READY"
        elif score >= 65:
            verdict = "REVIEW_READY"
        elif score >= 45:
            verdict = "WATCH_ONLY"
        else:
            verdict = "NOT_READY"

        return score, verdict, blockers, supports, cautions

    def _result(self, status, verdict, score, reason, payload):
        return {
            "module": "oracle_trade_readiness_report",
            "version": self.version,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "verdict": verdict,
            "readiness_score": round(float(score or 0), 2),
            "reason": reason,
            **payload,
            "compact_card": self._card(payload),
        }

    def _card(self, p):
        m = p.get("metrics", {})
        lines = [
            "🏁 ORACLE TRADE READINESS",
            f"Ticker: {p.get('ticker')}",
            f"Market: {p.get('title')}",
            "",
            f"Verdict: {p.get('verdict')}",
            f"Readiness Score: {p.get('readiness_score')}",
            f"Final Action: {m.get('oracle_final_action')}",
            "",
            f"Consensus: {m.get('consensus')} | {m.get('consensus_confidence')}%",
            f"Execution Gate: {m.get('execution_decision')}",
            f"EV: {m.get('ev_decision')} | {m.get('ev_score')}",
            f"Queue: {m.get('queue_decision')} | {m.get('queue_score')}",
            f"Portfolio: {m.get('portfolio_decision')} | {m.get('portfolio_score')}",
            f"Regime: {m.get('market_regime')}",
            f"Tradability: {m.get('tradability')} | Micro {m.get('microstructure_score')}",
            f"Order Book: {m.get('order_book_rating')} | Fill {m.get('fill_probability')}%",
            f"Flow: {m.get('flow_signal')} | {m.get('flow_score')}",
            "",
            f"Reason: {p.get('reason')}",
        ]

        if p.get("blockers"):
            lines.append("")
            lines.append("Blockers:")
            for b in p["blockers"][:8]:
                lines.append(f"- {b}")

        if p.get("cautions"):
            lines.append("")
            lines.append("Cautions:")
            for c in p["cautions"][:8]:
                lines.append(f"- {c}")

        if p.get("supports"):
            lines.append("")
            lines.append("Supports:")
            for s in p["supports"][:8]:
                lines.append(f"- {s}")

        return "\n".join(lines)

    def diagnostics(self):
        return {
            "module": "oracle_trade_readiness_report",
            "version": self.version,
            "status": "ok",
            "outputs": ["trade_readiness", "readiness_score", "readiness_card"],
        }


oracle_trade_readiness_report = OracleTradeReadinessReport()


if __name__ == "__main__":
    sample = {
        "ticker": "TEST",
        "title": "Sample readiness",
        "grade": "A-",
        "consensus_final_recommendation": "BUY YES",
        "consensus_confidence": 84,
        "execution_decision": "WATCH_ONLY",
        "tradability": "CAUTION",
        "microstructure_score": 68,
        "order_book_rating": "FAIR",
        "fill_probability": 55,
        "flow_signal": "IMPROVING_FLOW",
        "flow_score": 70,
        "portfolio_decision": "ALLOW",
        "portfolio_exposure_score": 90,
        "ev_decision": "WATCH_EV",
        "ev_score": 8,
        "oracle_final_action": "REVIEW",
    }

    import pprint
    pprint.pp(oracle_trade_readiness_report.build(sample, "TRENDING_EDGE"))
'''

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-060 Trade Readiness Report Integration
# ============================================================

try:
    from oracle_trade_readiness_report import oracle_trade_readiness_report
except Exception:
    oracle_trade_readiness_report = None


def _oracle060_apply_trade_readiness(ranked, market_regime=None):
    if oracle_trade_readiness_report is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            report = oracle_trade_readiness_report.build(item, market_regime)
            item["trade_readiness"] = report
            item["trade_readiness_verdict"] = report.get("verdict")
            item["trade_readiness_score"] = report.get("readiness_score")
            item["trade_readiness_card"] = report.get("compact_card")
        except Exception as exc:
            item["trade_readiness"] = {
                "status": "error",
                "verdict": "NOT_READY",
                "reason": str(exc),
            }
            item["trade_readiness_verdict"] = "NOT_READY"
            item["trade_readiness_score"] = 0

        enriched.append(item)

    rank = {
        "READY": 4,
        "REVIEW_READY": 3,
        "WATCH_ONLY": 2,
        "NOT_READY": 1,
    }

    enriched.sort(
        key=lambda x: (
            rank.get(x.get("trade_readiness_verdict"), 0),
            x.get("trade_readiness_score", 0) or 0,
            x.get("ev_score", 0) or 0,
        ) if isinstance(x, dict) else (0, 0, 0),
        reverse=True,
    )

    return enriched


def _oracle060_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked")
            regime = _state.get("market_regime")

            if isinstance(ranked, list):
                _state["last_ranked"] = _oracle060_apply_trade_readiness(ranked, regime)

                counts = {}
                for item in _state["last_ranked"]:
                    if isinstance(item, dict):
                        v = item.get("trade_readiness_verdict", "UNKNOWN")
                        counts[v] = counts.get(v, 0) + 1

                _state["trade_readiness_status"] = {
                    "status": "ok" if oracle_trade_readiness_report is not None else "missing",
                    "verdict_counts": counts,
                    "top": _state["last_ranked"][:5],
                }
            else:
                _state["trade_readiness_status"] = {"status": "no_ranked_data"}
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["trade_readiness_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle060_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle060_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle060_original_run_cycle(*args, **kwargs)
        _oracle060_enrich_state()
        return result


if "_oracle060_original_status" not in globals() and "status" in globals():
    _oracle060_original_status = status

    def status(*args, **kwargs):
        result = _oracle060_original_status(*args, **kwargs)
        _oracle060_enrich_state()

        if isinstance(result, dict):
            result["trade_readiness_status"] = (
                globals().get("_state", {}).get("trade_readiness_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = globals().get("_state", {}).get("last_ranked", result["last_ranked"])

        return result

# ============================================================
# END ORACLE-060
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle060_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-060 INSTALLER")
    print(" Trade Readiness Report")
    print("===================================")

    backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")
    print("[OK] Created oracle_trade_readiness_report.py")

    if not CONTINUOUS.exists():
        print("[WARN] oracle_continuous_intelligence.py not found; integration skipped")
    else:
        text = CONTINUOUS.read_text(encoding="utf-8", errors="ignore")
        if "ORACLE-060 Trade Readiness Report Integration" in text:
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
    print(" python oracle_trade_readiness_report.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('trade_readiness_status')); print(s.get('last_ranked',[{}])[0].get('trade_readiness_card'))\"")
    print("")
    print("[DONE] ORACLE-060 Trade Readiness Report installed")


if __name__ == "__main__":
    main()