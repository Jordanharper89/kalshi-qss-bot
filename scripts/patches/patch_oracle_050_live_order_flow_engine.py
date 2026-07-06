from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
ENGINE = ROOT / "oracle_order_flow_engine.py"
CONTINUOUS = ROOT / "oracle_continuous_intelligence.py"

ENGINE_CODE = r'''
"""
ORACLE-050 Live Order Flow Engine

Purpose:
- Track order-book/intelligence snapshots over time.
- Detect liquidity change, pressure shift, sweep risk,
  accumulation/distribution, and flow trend.
- Does NOT place trades.
"""

from datetime import datetime, UTC
from collections import defaultdict, deque
import json
from pathlib import Path

STATE_FILE = Path("oracle_order_flow_state.json")
MAX_HISTORY = 50


def _num(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _txt(value):
    return str(value or "").strip()


class OracleOrderFlowEngine:
    def __init__(self):
        self.version = "ORACLE-050"
        self.history = defaultdict(lambda: deque(maxlen=MAX_HISTORY))
        self._load()

    def analyze(self, opportunity):
        if not isinstance(opportunity, dict):
            return self._result("error", "UNKNOWN", 0, "Invalid opportunity object", {})

        ticker = (
            opportunity.get("ticker")
            or opportunity.get("market_ticker")
            or opportunity.get("title")
            or "UNKNOWN"
        )

        snapshot = self._build_snapshot(opportunity)
        self.history[ticker].append(snapshot)
        self._save()

        hist = list(self.history[ticker])
        analysis = self._analyze_history(hist)

        return self._result(
            "ok",
            analysis["flow_signal"],
            analysis["flow_score"],
            analysis["reason"],
            opportunity,
            snapshot=snapshot,
            history_count=len(hist),
            metrics=analysis["metrics"],
            risks=analysis["risks"],
            strengths=analysis["strengths"],
            flags=analysis["flags"],
        )

    def _build_snapshot(self, opportunity):
        obi = opportunity.get("order_book_intelligence") if isinstance(opportunity.get("order_book_intelligence"), dict) else {}
        micro = opportunity.get("microstructure") if isinstance(opportunity.get("microstructure"), dict) else {}

        metrics = obi.get("metrics") if isinstance(obi.get("metrics"), dict) else {}
        micro_metrics = micro.get("metrics") if isinstance(micro.get("metrics"), dict) else {}

        raw = opportunity.get("raw") if isinstance(opportunity.get("raw"), dict) else {}
        raw_raw = raw.get("raw") if isinstance(raw.get("raw"), dict) else {}

        edge = _num(metrics.get("raw_edge") or opportunity.get("edge") or raw.get("edge") or raw_raw.get("edge"), 0)
        tradable_edge = _num(metrics.get("tradable_edge"), max(0.0, edge))
        execution_cost = _num(metrics.get("execution_cost"), 0)
        fill_probability = _num(metrics.get("fill_probability"), 0)
        best_size = _num(metrics.get("best_execution_size"), 1)
        avg_depth = _num(metrics.get("avg_depth") or micro_metrics.get("avg_depth"), 0)
        volume = _num(metrics.get("volume") or opportunity.get("volume") or raw.get("volume"), 0)
        avg_spread = _num(micro_metrics.get("avg_spread"), 0)
        order_book_rating = _txt(opportunity.get("order_book_rating") or obi.get("order_book_rating"))
        tradability = _txt(opportunity.get("tradability") or micro.get("tradability"))
        confidence = _num(opportunity.get("confidence") or raw.get("confidence") or raw_raw.get("confidence"), 0)
        consensus_conf = _num(opportunity.get("consensus_confidence"), 0)

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "edge": edge,
            "tradable_edge": tradable_edge,
            "execution_cost": execution_cost,
            "fill_probability": fill_probability,
            "best_execution_size": best_size,
            "avg_depth": avg_depth,
            "volume": volume,
            "avg_spread": avg_spread,
            "order_book_rating": order_book_rating,
            "tradability": tradability,
            "confidence": confidence,
            "consensus_confidence": consensus_conf,
        }

    def _analyze_history(self, hist):
        latest = hist[-1]

        risks = []
        strengths = []
        flags = []

        if len(hist) < 2:
            return {
                "flow_signal": "NEW",
                "flow_score": 50.0,
                "reason": "Only one order-flow snapshot available; tracking started.",
                "metrics": {
                    "history_count": len(hist),
                    "depth_change": 0,
                    "fill_probability_change": 0,
                    "tradable_edge_change": 0,
                    "execution_cost_change": 0,
                },
                "risks": ["Insufficient order-flow history"],
                "strengths": [],
                "flags": ["tracking_started"],
            }

        first = hist[0]
        prev = hist[-2]

        depth_change = latest["avg_depth"] - prev["avg_depth"]
        fill_change = latest["fill_probability"] - prev["fill_probability"]
        edge_change = latest["tradable_edge"] - prev["tradable_edge"]
        cost_change = latest["execution_cost"] - prev["execution_cost"]
        spread_change = latest["avg_spread"] - prev["avg_spread"]

        depth_change_total = latest["avg_depth"] - first["avg_depth"]
        edge_change_total = latest["tradable_edge"] - first["tradable_edge"]
        fill_change_total = latest["fill_probability"] - first["fill_probability"]

        score = 50.0

        if depth_change > 2:
            score += 10
            strengths.append("Depth improved since prior snapshot")
        elif depth_change < -2:
            score -= 12
            risks.append("Depth deteriorated since prior snapshot")
            flags.append("liquidity_disappearing")

        if fill_change > 5:
            score += 10
            strengths.append("Fill probability improving")
        elif fill_change < -5:
            score -= 12
            risks.append("Fill probability deteriorating")
            flags.append("fill_probability_falling")

        if edge_change > 0.02:
            score += 8
            strengths.append("Tradable edge improving")
            flags.append("edge_expanding")
        elif edge_change < -0.02:
            score -= 10
            risks.append("Tradable edge compressing")
            flags.append("edge_compressing")

        if cost_change > 0.015:
            score -= 8
            risks.append("Execution cost rising")
            flags.append("execution_cost_rising")
        elif cost_change < -0.015:
            score += 6
            strengths.append("Execution cost falling")

        if spread_change > 0.02:
            score -= 8
            risks.append("Spread widening")
            flags.append("spread_widening")
        elif spread_change < -0.02:
            score += 6
            strengths.append("Spread tightening")

        if latest["fill_probability"] < 35:
            score -= 12
            risks.append("Current fill probability is weak")

        if latest["tradable_edge"] <= 0:
            score -= 20
            risks.append("No current tradable edge")
            flags.append("no_tradable_edge")
        elif latest["tradable_edge"] >= 0.10:
            score += 8
            strengths.append("Current tradable edge remains strong")

        if latest["order_book_rating"].upper() in ("UNUSABLE", ""):
            score -= 12
            risks.append("Current order-book rating is weak/unusable")

        if latest["tradability"].upper() in ("POOR", "UNTRADABLE", ""):
            score -= 10
            risks.append("Current microstructure tradability is poor/untradable")

        # Pattern detection
        if depth_change_total > 5 and edge_change_total > 0:
            flags.append("accumulation_possible")
            strengths.append("Depth and tradable edge improved over history")
            score += 8

        if depth_change_total < -5 and fill_change_total < -8:
            flags.append("distribution_or_liquidity_pull")
            risks.append("Depth and fill probability weakened over history")
            score -= 10

        if latest["avg_depth"] <= 2 and latest["fill_probability"] < 45:
            flags.append("thin_book_sweep_risk")
            risks.append("Thin book with low fill probability")

        score = max(0.0, min(100.0, score))

        if score >= 75:
            signal = "BULLISH_FLOW"
        elif score >= 60:
            signal = "IMPROVING_FLOW"
        elif score >= 45:
            signal = "NEUTRAL_FLOW"
        elif score >= 30:
            signal = "DETERIORATING_FLOW"
        else:
            signal = "AVOID_FLOW"

        reason = (
            f"Flow signal {signal} with score {score:.2f}. "
            f"Depth Δ {depth_change:.2f}, fill Δ {fill_change:.2f}, "
            f"tradable edge Δ {edge_change:.4f}, execution cost Δ {cost_change:.4f}."
        )

        return {
            "flow_signal": signal,
            "flow_score": round(score, 2),
            "reason": reason,
            "metrics": {
                "history_count": len(hist),
                "depth_change": round(depth_change, 6),
                "depth_change_total": round(depth_change_total, 6),
                "fill_probability_change": round(fill_change, 6),
                "fill_probability_change_total": round(fill_change_total, 6),
                "tradable_edge_change": round(edge_change, 6),
                "tradable_edge_change_total": round(edge_change_total, 6),
                "execution_cost_change": round(cost_change, 6),
                "spread_change": round(spread_change, 6),
                "latest_fill_probability": latest["fill_probability"],
                "latest_tradable_edge": latest["tradable_edge"],
                "latest_avg_depth": latest["avg_depth"],
            },
            "risks": risks,
            "strengths": strengths,
            "flags": flags,
        }

    def _result(self, status, signal, score, reason, opportunity, snapshot=None, history_count=0, metrics=None, risks=None, strengths=None, flags=None):
        opportunity = opportunity if isinstance(opportunity, dict) else {}

        return {
            "module": "oracle_order_flow_engine",
            "version": self.version,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "ticker": opportunity.get("ticker"),
            "title": opportunity.get("title"),
            "flow_signal": signal,
            "flow_score": round(float(score or 0), 2),
            "reason": reason,
            "history_count": history_count,
            "snapshot": snapshot or {},
            "metrics": metrics or {},
            "risks": risks or [],
            "strengths": strengths or [],
            "flags": flags or [],
            "compact_card": self._card(opportunity, signal, score, reason, history_count, metrics or {}, risks or [], strengths or [], flags or []),
        }

    def _card(self, opportunity, signal, score, reason, history_count, metrics, risks, strengths, flags):
        lines = [
            "🌊 ORACLE ORDER FLOW",
            f"Ticker: {opportunity.get('ticker', 'UNKNOWN')}",
            f"Market: {opportunity.get('title', 'Untitled opportunity')}",
            "",
            f"Flow Signal: {signal}",
            f"Flow Score: {round(float(score or 0), 2)}",
            f"Snapshots: {history_count}",
            "",
            f"Depth Δ: {metrics.get('depth_change')}",
            f"Fill Δ: {metrics.get('fill_probability_change')}",
            f"Tradable Edge Δ: {metrics.get('tradable_edge_change')}",
            f"Execution Cost Δ: {metrics.get('execution_cost_change')}",
            "",
            f"Reason: {reason}",
        ]

        if flags:
            lines.append("")
            lines.append("Flags:")
            for f in flags[:6]:
                lines.append(f"- {f}")

        if risks:
            lines.append("")
            lines.append("Risks:")
            for r in risks[:6]:
                lines.append(f"- {r}")

        if strengths:
            lines.append("")
            lines.append("Strengths:")
            for s in strengths[:6]:
                lines.append(f"- {s}")

        return "\n".join(lines)

    def _save(self):
        try:
            data = {}
            for ticker, hist in self.history.items():
                data[ticker] = list(hist)[-MAX_HISTORY:]
            STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load(self):
        try:
            if not STATE_FILE.exists():
                return
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for ticker, hist in data.items():
                    if isinstance(hist, list):
                        self.history[ticker] = deque(hist[-MAX_HISTORY:], maxlen=MAX_HISTORY)
        except Exception:
            pass

    def diagnostics(self):
        return {
            "module": "oracle_order_flow_engine",
            "version": self.version,
            "status": "ok",
            "tracked_tickers": len(self.history),
            "state_file": str(STATE_FILE),
            "max_history": MAX_HISTORY,
        }


oracle_order_flow_engine = OracleOrderFlowEngine()


if __name__ == "__main__":
    sample = {
        "ticker": "TEST",
        "title": "Sample order flow",
        "edge": 0.12,
        "confidence": 90,
        "order_book_rating": "WEAK",
        "tradability": "POOR",
        "order_book_intelligence": {
            "metrics": {
                "raw_edge": 0.12,
                "tradable_edge": 0.06,
                "execution_cost": 0.04,
                "fill_probability": 43,
                "best_execution_size": 1,
                "avg_depth": 2,
            }
        },
        "microstructure": {
            "metrics": {
                "avg_spread": 0.04
            }
        }
    }

    result = oracle_order_flow_engine.analyze(sample)
    print(result["compact_card"])
    print(result)
'''

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-050 Live Order Flow Integration
# ============================================================

try:
    from oracle_order_flow_engine import oracle_order_flow_engine
except Exception:
    oracle_order_flow_engine = None


def _oracle050_apply_order_flow(ranked):
    if oracle_order_flow_engine is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            flow = oracle_order_flow_engine.analyze(item)
            item["order_flow"] = flow
            item["flow_signal"] = flow.get("flow_signal")
            item["flow_score"] = flow.get("flow_score")
            item["flow_flags"] = flow.get("flags", [])
            item["order_flow_card"] = flow.get("compact_card")
        except Exception as exc:
            item["order_flow"] = {
                "status": "error",
                "flow_signal": "UNKNOWN",
                "reason": str(exc),
            }
            item["flow_signal"] = "UNKNOWN"
            item["flow_score"] = 0

        enriched.append(item)

    flow_rank = {
        "BULLISH_FLOW": 5,
        "IMPROVING_FLOW": 4,
        "NEUTRAL_FLOW": 3,
        "DETERIORATING_FLOW": 2,
        "AVOID_FLOW": 1,
        "NEW": 3,
        "UNKNOWN": 0,
    }

    enriched.sort(
        key=lambda x: (
            flow_rank.get(x.get("flow_signal"), 0),
            x.get("flow_score", 0) or 0,
            x.get("tradable_edge", 0) or 0,
            x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0))),
        ) if isinstance(x, dict) else (0, 0, 0, 0),
        reverse=True,
    )

    return enriched


def _oracle050_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            if isinstance(_state.get("last_ranked"), list):
                _state["last_ranked"] = _oracle050_apply_order_flow(_state["last_ranked"])

            ranked = _state.get("last_ranked") or []
            counts = {}
            for item in ranked:
                if isinstance(item, dict):
                    sig = item.get("flow_signal", "UNKNOWN")
                    counts[sig] = counts.get(sig, 0) + 1

            _state["order_flow_status"] = {
                "status": "ok" if oracle_order_flow_engine is not None else "missing",
                "flow_counts": counts,
                "top": ranked[:5],
            }
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["order_flow_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle050_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle050_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle050_original_run_cycle(*args, **kwargs)
        _oracle050_enrich_state()
        return result


if "_oracle050_original_status" not in globals() and "status" in globals():
    _oracle050_original_status = status

    def status(*args, **kwargs):
        result = _oracle050_original_status(*args, **kwargs)
        _oracle050_enrich_state()

        if isinstance(result, dict):
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = _oracle050_apply_order_flow(result["last_ranked"])

            if isinstance(result.get("pipeline_status"), dict):
                ps = result["pipeline_status"]
                if isinstance(ps.get("last_ranked"), list):
                    ps["last_ranked"] = _oracle050_apply_order_flow(ps["last_ranked"])

            result["order_flow_status"] = (
                globals().get("_state", {}).get("order_flow_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )

        return result

# ============================================================
# END ORACLE-050
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle050_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-050 INSTALLER")
    print(" Live Order Flow Engine")
    print("===================================")

    backup(ENGINE)
    ENGINE.write_text(ENGINE_CODE, encoding="utf-8")
    print("[OK] Created oracle_order_flow_engine.py")

    if not CONTINUOUS.exists():
        print("[WARN] oracle_continuous_intelligence.py not found; integration skipped")
    else:
        text = CONTINUOUS.read_text(encoding="utf-8", errors="ignore")
        if "ORACLE-050 Live Order Flow Integration" in text:
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
    print(" python oracle_order_flow_engine.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('order_flow_status')); print(s.get('last_ranked',[{}])[0].get('order_flow_card'))\"")
    print("")
    print("[DONE] ORACLE-050 Live Order Flow Engine installed")


if __name__ == "__main__":
    main()