
"""
ORACLE-055 Execution Queue Manager

Purpose:
- Stage Oracle opportunities into a safe execution/review/watch queue.
- Does NOT place trades.
- Respects Gatekeeper, Policy, Microstructure, Portfolio Exposure, and Alerts.
"""

from datetime import datetime, UTC
from pathlib import Path
import json
import hashlib

STATE_FILE = Path("oracle_execution_queue_state.json")
MAX_QUEUE = 250


def _txt(v):
    return str(v or "").strip()


def _num(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


class OracleExecutionQueueManager:
    def __init__(self):
        self.version = "ORACLE-055"
        self.state = {
            "queue": [],
            "rejected": [],
            "history": [],
        }
        self._load()

    def build_queue(self, ranked, smart_alerts=None):
        ranked = ranked if isinstance(ranked, list) else []
        smart_alerts = smart_alerts if isinstance(smart_alerts, list) else []

        alert_map = {}
        for a in smart_alerts:
            if isinstance(a, dict):
                alert_map[a.get("ticker")] = a

        new_queue = []
        rejected = []

        for item in ranked:
            if not isinstance(item, dict):
                continue

            candidate = self._candidate(item, alert_map.get(item.get("ticker")))
            decision = self._queue_decision(candidate)

            candidate["queue_decision"] = decision["decision"]
            candidate["queue_score"] = decision["score"]
            candidate["queue_reason"] = decision["reason"]
            candidate["queue_flags"] = decision["flags"]
            candidate["compact_card"] = self._card(candidate)

            if decision["decision"] in ("EXECUTION_READY", "REVIEW_REQUIRED", "WATCH_QUEUE"):
                new_queue.append(candidate)
            else:
                rejected.append(candidate)

        new_queue.sort(key=lambda x: x.get("queue_score", 0), reverse=True)
        rejected.sort(key=lambda x: x.get("queue_score", 0), reverse=True)

        self.state["queue"] = self._dedupe(new_queue)[:MAX_QUEUE]
        self.state["rejected"] = self._dedupe(rejected)[:MAX_QUEUE]

        summary = {
            "timestamp": datetime.now(UTC).isoformat(),
            "queued": len(self.state["queue"]),
            "rejected": len(self.state["rejected"]),
            "counts": self._counts(self.state["queue"]),
        }

        self.state["history"].append(summary)
        self.state["history"] = self.state["history"][-200:]
        self._save()

        return {
            "module": "oracle_execution_queue_manager",
            "version": self.version,
            "status": "ok",
            "timestamp": summary["timestamp"],
            "queued": len(self.state["queue"]),
            "rejected": len(self.state["rejected"]),
            "counts": summary["counts"],
            "queue": self.state["queue"][:25],
            "rejected_top": self.state["rejected"][:10],
            "state_file": str(STATE_FILE),
        }

    def _candidate(self, item, alert):
        portfolio = item.get("portfolio_exposure") if isinstance(item.get("portfolio_exposure"), dict) else {}
        policy = item.get("execution_gate", {}).get("execution_policy") if isinstance(item.get("execution_gate"), dict) else {}
        if not isinstance(policy, dict):
            policy = {}
        policy_data = policy.get("policy")
        if not isinstance(policy_data, dict):
            policy_data = {}

        ticker = item.get("ticker")
        title = item.get("title")

        key_raw = f"{ticker}|{title}|{item.get('consensus_final_recommendation')}|{item.get('execution_decision')}"
        queue_id = hashlib.sha1(key_raw.encode("utf-8", errors="ignore")).hexdigest()[:16]

        return {
            "queue_id": queue_id,
            "ticker": ticker,
            "title": title,
            "side": _txt(item.get("side") or item.get("consensus_final_recommendation") or "WATCH").upper(),
            "grade": _txt(item.get("grade")).upper(),
            "risk": _txt(item.get("risk")).upper(),
            "edge": _num(item.get("edge"), 0),
            "adaptive_score": _num(item.get("adaptive_score") or item.get("overall_score"), 0),
            "consensus": _txt(item.get("consensus_final_recommendation")).upper(),
            "consensus_confidence": _num(item.get("consensus_confidence"), 0),
            "consensus_strength": _txt(item.get("consensus_strength")).upper(),
            "execution_decision": _txt(item.get("execution_decision")).upper(),
            "policy_profile": _txt(
                item.get("execution_gate", {}).get("policy_profile")
                if isinstance(item.get("execution_gate"), dict)
                else ""
            ).upper(),
            "policy_mode": _txt(policy_data.get("profile")).upper(),
            "tradability": _txt(item.get("tradability")).upper(),
            "microstructure_score": _num(item.get("microstructure_score"), 0),
            "order_book_rating": _txt(item.get("order_book_rating")).upper(),
            "order_book_score": _num(item.get("order_book_score"), 0),
            "tradable_edge": _num(item.get("tradable_edge"), 0),
            "fill_probability": _num(item.get("fill_probability"), 0),
            "flow_signal": _txt(item.get("flow_signal")).upper(),
            "flow_score": _num(item.get("flow_score"), 0),
            "lifecycle_state": _txt(item.get("lifecycle_state")).upper(),
            "lifecycle_score": _num(item.get("lifecycle_score"), 0),
            "portfolio_decision": _txt(item.get("portfolio_decision") or portfolio.get("decision")).upper(),
            "portfolio_score": _num(item.get("portfolio_exposure_score") or portfolio.get("score"), 0),
            "alert_priority": _txt(alert.get("priority") if isinstance(alert, dict) else "").upper(),
            "alert_score": _num(alert.get("priority_score") if isinstance(alert, dict) else 0, 0),
            "created_at": datetime.now(UTC).isoformat(),
        }

    def _queue_decision(self, c):
        score = 0.0
        flags = []

        if c["execution_decision"] == "EXECUTE":
            score += 60
            flags.append("gatekeeper_execute")
        elif c["execution_decision"] == "REQUIRES_REVIEW":
            score += 40
            flags.append("gatekeeper_review")
        elif c["execution_decision"] == "WATCH_ONLY":
            score += 25
            flags.append("gatekeeper_watch")
        elif c["execution_decision"] == "BLOCK":
            score -= 40
            flags.append("gatekeeper_block")

        if c["consensus"] in ("BUY YES", "BUY NO"):
            score += 25
            flags.append("directional_consensus")
        elif c["consensus"] == "WATCH":
            score += 8
            flags.append("watch_consensus")
        elif c["consensus"] == "PASS":
            score -= 25
            flags.append("pass_consensus")

        if c["consensus_confidence"] >= 82:
            score += 18
            flags.append("high_consensus_confidence")
        elif c["consensus_confidence"] >= 70:
            score += 8
            flags.append("acceptable_consensus_confidence")
        elif c["consensus_confidence"] < 55:
            score -= 12
            flags.append("low_consensus_confidence")

        if c["grade"] in ("A+", "A", "A-", "B+"):
            score += 15
            flags.append("tradeable_grade")
        elif c["grade"] == "PASS":
            score -= 20
            flags.append("pass_grade")

        if c["tradability"] == "GOOD":
            score += 20
            flags.append("good_tradability")
        elif c["tradability"] == "CAUTION":
            score += 8
            flags.append("caution_tradability")
        elif c["tradability"] in ("POOR", "UNTRADABLE"):
            score -= 25
            flags.append("weak_tradability")

        if c["order_book_rating"] == "GOOD":
            score += 15
            flags.append("good_order_book")
        elif c["order_book_rating"] == "FAIR":
            score += 8
            flags.append("fair_order_book")
        elif c["order_book_rating"] in ("WEAK", "UNUSABLE"):
            score -= 18
            flags.append("weak_order_book")

        if c["fill_probability"] >= 65:
            score += 12
            flags.append("good_fill_probability")
        elif c["fill_probability"] < 35:
            score -= 12
            flags.append("weak_fill_probability")

        if c["tradable_edge"] >= 0.10:
            score += 12
            flags.append("strong_tradable_edge")
        elif c["tradable_edge"] <= 0:
            score -= 20
            flags.append("no_tradable_edge")

        if c["flow_signal"] in ("BULLISH_FLOW", "IMPROVING_FLOW"):
            score += 12
            flags.append("positive_flow")
        elif c["flow_signal"] in ("DETERIORATING_FLOW", "AVOID_FLOW"):
            score -= 12
            flags.append("weak_flow")

        if c["lifecycle_state"] == "EXECUTION_READY":
            score += 25
            flags.append("lifecycle_execution_ready")
        elif c["lifecycle_state"] == "IMPROVING":
            score += 15
            flags.append("lifecycle_improving")
        elif c["lifecycle_state"] == "ACTIVE":
            score += 8
            flags.append("lifecycle_active")
        elif c["lifecycle_state"] in ("BLOCKED", "STALE"):
            score -= 18
            flags.append("lifecycle_blocked_or_stale")

        if c["portfolio_decision"] == "ALLOW":
            score += 12
            flags.append("portfolio_allow")
        elif c["portfolio_decision"] == "LIMIT_SIZE":
            score += 4
            flags.append("portfolio_limit_size")
        elif c["portfolio_decision"] == "REVIEW":
            score -= 8
            flags.append("portfolio_review")
        elif c["portfolio_decision"] == "BLOCK_EXPOSURE":
            score -= 25
            flags.append("portfolio_block_exposure")

        if c["alert_priority"] == "CRITICAL":
            score += 20
            flags.append("critical_alert")
        elif c["alert_priority"] == "HIGH":
            score += 12
            flags.append("high_alert")
        elif c["alert_priority"] == "MEDIUM":
            score += 5
            flags.append("medium_alert")

        if c["risk"] == "HIGH":
            score -= 20
            flags.append("high_risk")

        if (
            c["execution_decision"] == "EXECUTE"
            and c["portfolio_decision"] in ("ALLOW", "LIMIT_SIZE")
            and c["tradability"] in ("GOOD", "CAUTION")
            and c["order_book_rating"] in ("GOOD", "FAIR")
            and c["fill_probability"] >= 45
            and c["tradable_edge"] > 0
        ):
            decision = "EXECUTION_READY"
        elif score >= 70 and c["execution_decision"] in ("EXECUTE", "REQUIRES_REVIEW", "WATCH_ONLY"):
            decision = "REVIEW_REQUIRED"
        elif score >= 35 and c["execution_decision"] in ("WATCH_ONLY", "REQUIRES_REVIEW"):
            decision = "WATCH_QUEUE"
        else:
            decision = "REJECTED"

        return {
            "decision": decision,
            "score": round(max(0.0, min(100.0, score)), 2),
            "flags": flags,
            "reason": f"Queue decision {decision} with score {round(max(0.0, min(100.0, score)), 2)}.",
        }

    def _dedupe(self, rows):
        best = {}
        for r in rows:
            key = r.get("queue_id")
            if key not in best or r.get("queue_score", 0) > best[key].get("queue_score", 0):
                best[key] = r
        return list(best.values())

    def _counts(self, queue):
        counts = {}
        for q in queue:
            d = q.get("queue_decision", "UNKNOWN")
            counts[d] = counts.get(d, 0) + 1
        return counts

    def _card(self, c):
        return "\n".join([
            "🧾 ORACLE EXECUTION QUEUE",
            f"Queue ID: {c.get('queue_id')}",
            f"Ticker: {c.get('ticker')}",
            f"Market: {c.get('title')}",
            "",
            f"Queue Decision: {c.get('queue_decision')}",
            f"Queue Score: {c.get('queue_score')}",
            f"Reason: {c.get('queue_reason')}",
            "",
            f"Side: {c.get('side')}",
            f"Consensus: {c.get('consensus')} | {c.get('consensus_confidence')}%",
            f"Execution Gate: {c.get('execution_decision')}",
            f"Policy: {c.get('policy_profile') or c.get('policy_mode')}",
            f"Portfolio: {c.get('portfolio_decision')} | {c.get('portfolio_score')}",
            f"Tradability: {c.get('tradability')} | Micro {c.get('microstructure_score')}",
            f"Order Book: {c.get('order_book_rating')} | Fill {c.get('fill_probability')}%",
            f"Flow: {c.get('flow_signal')} | {c.get('flow_score')}",
            "",
            "Flags:",
            *[f"- {f}" for f in c.get("queue_flags", [])[:10]],
        ])

    def diagnostics(self):
        return {
            "module": "oracle_execution_queue_manager",
            "version": self.version,
            "status": "ok",
            "queued": len(self.state.get("queue", [])),
            "rejected": len(self.state.get("rejected", [])),
            "state_file": str(STATE_FILE),
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


oracle_execution_queue_manager = OracleExecutionQueueManager()




# ============================================================
# ORACLE-059 EV Queue Calibration
# ============================================================

if "OracleExecutionQueueManager" in globals():
    if "_oracle059_original_queue_decision" not in globals():
        _oracle059_original_queue_decision = OracleExecutionQueueManager._queue_decision

        def _oracle059_queue_decision(self, c):
            base = _oracle059_original_queue_decision(self, c)
            if not isinstance(base, dict):
                return base

            ev_decision = str(c.get("ev_decision") or "").upper()
            ev_score = float(c.get("ev_score") or 0)

            original = base.get("decision", "REJECTED")
            decision = original
            reason = base.get("reason", "")
            flags = list(base.get("flags", []))
            score = float(base.get("score") or 0)

            if ev_decision == "NEGATIVE_EV":
                decision = "REJECTED"
                score = min(score, 15)
                flags.append("negative_ev_block")
                reason += " EV overlay rejected negative EV candidate."

            elif ev_decision == "WEAK_EV":
                if decision == "EXECUTION_READY":
                    decision = "REVIEW_REQUIRED"
                    flags.append("weak_ev_downgrade")
                    reason += " EV overlay downgraded execution-ready to review."
                score = min(score, 65)

            elif ev_decision == "WATCH_EV":
                if decision == "EXECUTION_READY" and ev_score < 10:
                    decision = "REVIEW_REQUIRED"
                    flags.append("watch_ev_review_required")
                    reason += " EV overlay requires review because EV is only WATCH_EV."

            elif ev_decision == "POSITIVE_EV":
                score = min(100, score + 8)
                flags.append("positive_ev_support")
                reason += " EV overlay supports queue priority."

            base["decision"] = decision
            base["score"] = round(max(0, min(100, score)), 2)
            base["reason"] = reason.strip()
            base["flags"] = flags
            base["ev_overlay"] = {
                "version": "ORACLE-059",
                "status": "applied",
                "ev_decision": ev_decision,
                "ev_score": ev_score,
                "original_queue_decision": original,
                "final_queue_decision": decision,
            }
            return base

        OracleExecutionQueueManager._queue_decision = _oracle059_queue_decision


if "OracleExecutionQueueManager" in globals():
    if "_oracle059_original_candidate" not in globals():
        _oracle059_original_candidate = OracleExecutionQueueManager._candidate

        def _oracle059_candidate(self, item, alert):
            c = _oracle059_original_candidate(self, item, alert)
            if isinstance(c, dict):
                c["ev_decision"] = str(item.get("ev_decision") or "").upper()
                c["ev_score"] = float(item.get("ev_score") or 0)
            return c

        OracleExecutionQueueManager._candidate = _oracle059_candidate

# ============================================================
# END ORACLE-059
# ============================================================


if __name__ == "__main__":
    sample = [{
        "ticker": "TEST",
        "title": "Sample queue opportunity",
        "side": "BUY YES",
        "grade": "A-",
        "risk": "MEDIUM",
        "adaptive_score": 82,
        "consensus_final_recommendation": "BUY YES",
        "consensus_confidence": 84,
        "consensus_strength": "STRONG",
        "execution_decision": "WATCH_ONLY",
        "tradability": "CAUTION",
        "microstructure_score": 67,
        "order_book_rating": "FAIR",
        "order_book_score": 70,
        "tradable_edge": 0.08,
        "fill_probability": 55,
        "flow_signal": "IMPROVING_FLOW",
        "flow_score": 70,
        "lifecycle_state": "IMPROVING",
        "lifecycle_score": 76,
        "portfolio_decision": "ALLOW",
        "portfolio_exposure_score": 90,
    }]

    import pprint
    pprint.pp(oracle_execution_queue_manager.build_queue(sample, []))
