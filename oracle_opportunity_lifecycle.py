
"""
ORACLE-052 Opportunity Lifecycle Tracker

Purpose:
- Classify each opportunity lifecycle state:
  NEW, ACTIVE, IMPROVING, DECAYING, STALE, BLOCKED, EXECUTION_READY
- Uses Live Monitor + Consensus + Gatekeeper + Microstructure + Order Flow.
- Does NOT execute trades.
"""

from datetime import datetime, UTC
from pathlib import Path
import json
import time

STATE_FILE = Path("oracle_opportunity_lifecycle_state.json")
STALE_AFTER_SECONDS = 900


def _num(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _txt(v):
    return str(v or "").strip()


class OracleOpportunityLifecycleTracker:
    def __init__(self):
        self.version = "ORACLE-052"
        self.state = {"opportunities": {}}
        self._load()

    def update(self, ranked):
        if not isinstance(ranked, list):
            return self._status([], "invalid ranked list")

        updated = []

        for item in ranked:
            if not isinstance(item, dict):
                continue

            key = item.get("ticker") or item.get("title") or "UNKNOWN"
            now = time.time()
            old = self.state["opportunities"].get(key)
            snap = self._snapshot(item, now)

            lifecycle = self._classify(old, snap)
            snap["lifecycle_state"] = lifecycle["state"]
            snap["lifecycle_reason"] = lifecycle["reason"]
            snap["lifecycle_score"] = lifecycle["score"]
            snap["lifecycle_flags"] = lifecycle["flags"]
            snap["updated_at"] = datetime.now(UTC).isoformat()

            if old is None:
                snap["first_seen"] = now
                snap["seen_count"] = 1
            else:
                snap["first_seen"] = old.get("first_seen", now)
                snap["seen_count"] = int(old.get("seen_count", 0)) + 1

            self.state["opportunities"][key] = snap

            item["lifecycle"] = {
                "module": "oracle_opportunity_lifecycle",
                "version": self.version,
                "status": "ok",
                "state": snap["lifecycle_state"],
                "score": snap["lifecycle_score"],
                "reason": snap["lifecycle_reason"],
                "flags": snap["lifecycle_flags"],
                "seen_count": snap["seen_count"],
                "first_seen": snap["first_seen"],
                "compact_card": self._card(item, snap),
            }

            item["lifecycle_state"] = snap["lifecycle_state"]
            item["lifecycle_score"] = snap["lifecycle_score"]
            item["lifecycle_card"] = item["lifecycle"]["compact_card"]
            updated.append(item)

        self._save()
        return self._status(updated, "ok")

    def _snapshot(self, item, now):
        return {
            "ticker": item.get("ticker"),
            "title": item.get("title"),
            "timestamp_epoch": now,
            "grade": _txt(item.get("grade")),
            "risk": _txt(item.get("risk")),
            "edge": _num(item.get("edge"), 0),
            "adaptive_score": _num(item.get("adaptive_score") or item.get("overall_score"), 0),
            "consensus": _txt(item.get("consensus_final_recommendation")),
            "consensus_confidence": _num(item.get("consensus_confidence"), 0),
            "execution_decision": _txt(item.get("execution_decision")),
            "tradability": _txt(item.get("tradability")),
            "microstructure_score": _num(item.get("microstructure_score"), 0),
            "order_book_rating": _txt(item.get("order_book_rating")),
            "tradable_edge": _num(item.get("tradable_edge"), 0),
            "fill_probability": _num(item.get("fill_probability"), 0),
            "flow_signal": _txt(item.get("flow_signal")),
            "flow_score": _num(item.get("flow_score"), 0),
        }

    def _classify(self, old, new):
        flags = []
        score = 50.0

        if old is None:
            return {
                "state": "NEW",
                "score": 50.0,
                "reason": "Opportunity first observed by lifecycle tracker.",
                "flags": ["first_seen"],
            }

        age = new["timestamp_epoch"] - _num(old.get("timestamp_epoch"), new["timestamp_epoch"])
        if age > STALE_AFTER_SECONDS:
            flags.append("stale_observation")
            score -= 20

        edge_delta = new["edge"] - _num(old.get("edge"), 0)
        adaptive_delta = new["adaptive_score"] - _num(old.get("adaptive_score"), 0)
        conf_delta = new["consensus_confidence"] - _num(old.get("consensus_confidence"), 0)
        tradable_delta = new["tradable_edge"] - _num(old.get("tradable_edge"), 0)
        flow_delta = new["flow_score"] - _num(old.get("flow_score"), 0)

        if new["execution_decision"] == "EXECUTE":
            score += 35
            flags.append("execution_ready")
            return {
                "state": "EXECUTION_READY",
                "score": min(100, score),
                "reason": "Gatekeeper marks this opportunity as execution-ready.",
                "flags": flags,
            }

        if new["execution_decision"] == "BLOCK":
            score -= 18
            flags.append("blocked_by_gatekeeper")

        if new["grade"] == "PASS":
            score -= 12
            flags.append("pass_grade")

        if new["tradability"] in ("POOR", "UNTRADABLE"):
            score -= 12
            flags.append("weak_tradability")

        if new["order_book_rating"] in ("WEAK", "UNUSABLE"):
            score -= 10
            flags.append("weak_order_book")

        if new["flow_signal"] in ("BULLISH_FLOW", "IMPROVING_FLOW"):
            score += 15
            flags.append("positive_order_flow")
        elif new["flow_signal"] in ("DETERIORATING_FLOW", "AVOID_FLOW"):
            score -= 15
            flags.append("negative_order_flow")

        if edge_delta > 0.05:
            score += 8
            flags.append("edge_expanding")
        elif edge_delta < -0.05:
            score -= 8
            flags.append("edge_decaying")

        if adaptive_delta > 5:
            score += 8
            flags.append("score_improving")
        elif adaptive_delta < -5:
            score -= 8
            flags.append("score_decaying")

        if conf_delta > 6:
            score += 8
            flags.append("confidence_improving")
        elif conf_delta < -6:
            score -= 8
            flags.append("confidence_decaying")

        if tradable_delta > 0.04:
            score += 10
            flags.append("tradable_edge_improving")
        elif tradable_delta < -0.04:
            score -= 10
            flags.append("tradable_edge_decaying")

        if flow_delta > 12:
            score += 8
            flags.append("flow_improving")
        elif flow_delta < -12:
            score -= 8
            flags.append("flow_decaying")

        score = max(0.0, min(100.0, score))

        if "stale_observation" in flags:
            state = "STALE"
        elif score >= 75:
            state = "IMPROVING"
        elif score >= 55:
            state = "ACTIVE"
        elif score >= 35:
            state = "DECAYING"
        else:
            state = "BLOCKED"

        return {
            "state": state,
            "score": round(score, 2),
            "reason": (
                f"Lifecycle {state}. Δedge={edge_delta:.4f}, "
                f"Δscore={adaptive_delta:.2f}, Δconf={conf_delta:.2f}, "
                f"Δtradable_edge={tradable_delta:.4f}, Δflow={flow_delta:.2f}."
            ),
            "flags": flags,
        }

    def _card(self, item, snap):
        return "\n".join([
            "🧬 ORACLE LIFECYCLE",
            f"Ticker: {snap.get('ticker')}",
            f"Market: {snap.get('title')}",
            "",
            f"State: {snap.get('lifecycle_state')}",
            f"Score: {snap.get('lifecycle_score')}",
            f"Seen Count: {snap.get('seen_count')}",
            "",
            f"Consensus: {snap.get('consensus')} | {snap.get('consensus_confidence')}%",
            f"Execution: {snap.get('execution_decision')}",
            f"Tradability: {snap.get('tradability')}",
            f"Order Flow: {snap.get('flow_signal')} | {snap.get('flow_score')}",
            "",
            f"Reason: {snap.get('lifecycle_reason')}",
        ])

    def _status(self, updated, status):
        counts = {}
        for v in self.state.get("opportunities", {}).values():
            s = v.get("lifecycle_state", "UNKNOWN")
            counts[s] = counts.get(s, 0) + 1

        return {
            "module": "oracle_opportunity_lifecycle",
            "version": self.version,
            "status": status,
            "tracked": len(self.state.get("opportunities", {})),
            "lifecycle_counts": counts,
            "updated_count": len(updated),
            "top": updated[:5],
            "state_file": str(STATE_FILE),
        }

    def diagnostics(self):
        return self._status([], "ok")

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


oracle_opportunity_lifecycle = OracleOpportunityLifecycleTracker()


if __name__ == "__main__":
    sample = [{
        "ticker": "TEST",
        "title": "Sample lifecycle opportunity",
        "grade": "B+",
        "risk": "MEDIUM",
        "edge": 0.12,
        "adaptive_score": 65,
        "consensus_final_recommendation": "WATCH",
        "consensus_confidence": 67,
        "execution_decision": "WATCH_ONLY",
        "tradability": "CAUTION",
        "microstructure_score": 64,
        "order_book_rating": "FAIR",
        "tradable_edge": 0.08,
        "fill_probability": 55,
        "flow_signal": "IMPROVING_FLOW",
        "flow_score": 62,
    }]

    import pprint
    pprint.pp(oracle_opportunity_lifecycle.update(sample))
