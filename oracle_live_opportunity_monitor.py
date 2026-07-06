
"""
ORACLE-051 Live Opportunity Monitor

Purpose:
- Track opportunities across Oracle cycles.
- Detect meaningful changes:
  confidence jumps, consensus changes, execution changes,
  liquidity/tradability improvement, flow changes, and edge decay.
- Does NOT execute trades.
"""

from datetime import datetime, UTC
from pathlib import Path
import json

STATE_FILE = Path("oracle_live_opportunity_monitor_state.json")
MAX_EVENTS = 500


def _num(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _txt(v):
    return str(v or "").strip()


class OracleLiveOpportunityMonitor:
    def __init__(self):
        self.version = "ORACLE-051"
        self.state = {
            "opportunities": {},
            "events": [],
        }
        self._load()

    def observe(self, ranked):
        if not isinstance(ranked, list):
            return self._status([], "Invalid ranked list")

        new_events = []

        for item in ranked:
            if not isinstance(item, dict):
                continue

            key = self._key(item)
            snap = self._snapshot(item)
            old = self.state["opportunities"].get(key)

            events = self._detect_events(key, old, snap, item)
            new_events.extend(events)

            self.state["opportunities"][key] = snap

        if new_events:
            self.state["events"].extend(new_events)
            self.state["events"] = self.state["events"][-MAX_EVENTS:]

        self._save()
        return self._status(new_events, "ok")

    def _key(self, item):
        return (
            item.get("ticker")
            or item.get("market_ticker")
            or item.get("title")
            or "UNKNOWN"
        )

    def _snapshot(self, item):
        consensus = item.get("consensus") if isinstance(item.get("consensus"), dict) else {}
        gate = item.get("execution_gate") if isinstance(item.get("execution_gate"), dict) else {}
        micro = item.get("microstructure") if isinstance(item.get("microstructure"), dict) else {}
        obi = item.get("order_book_intelligence") if isinstance(item.get("order_book_intelligence"), dict) else {}
        flow = item.get("order_flow") if isinstance(item.get("order_flow"), dict) else {}

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "ticker": item.get("ticker"),
            "title": item.get("title"),
            "grade": item.get("grade"),
            "risk": item.get("risk"),
            "edge": _num(item.get("edge"), 0),
            "adaptive_score": _num(item.get("adaptive_score") or item.get("overall_score"), 0),
            "consensus_final_recommendation": _txt(
                item.get("consensus_final_recommendation")
                or consensus.get("final_recommendation")
            ),
            "consensus_confidence": _num(
                item.get("consensus_confidence")
                or consensus.get("consensus_confidence"),
                0,
            ),
            "consensus_strength": _txt(
                item.get("consensus_strength")
                or consensus.get("consensus_strength")
            ),
            "execution_decision": _txt(
                item.get("execution_decision")
                or gate.get("execution_decision")
            ),
            "tradability": _txt(item.get("tradability") or micro.get("tradability")),
            "microstructure_score": _num(item.get("microstructure_score") or micro.get("microstructure_score"), 0),
            "order_book_rating": _txt(item.get("order_book_rating") or obi.get("order_book_rating")),
            "order_book_score": _num(item.get("order_book_score") or obi.get("score"), 0),
            "tradable_edge": _num(item.get("tradable_edge") or (obi.get("metrics") or {}).get("tradable_edge"), 0),
            "fill_probability": _num(item.get("fill_probability") or (obi.get("metrics") or {}).get("fill_probability"), 0),
            "flow_signal": _txt(item.get("flow_signal") or flow.get("flow_signal")),
            "flow_score": _num(item.get("flow_score") or flow.get("flow_score"), 0),
        }

    def _detect_events(self, key, old, new, item):
        if old is None:
            return [self._event(
                "NEW_OPPORTUNITY",
                key,
                "New opportunity entered live monitor.",
                new,
                item,
                severity="INFO",
            )]

        events = []

        conf_delta = new["consensus_confidence"] - _num(old.get("consensus_confidence"), 0)
        edge_delta = new["edge"] - _num(old.get("edge"), 0)
        adaptive_delta = new["adaptive_score"] - _num(old.get("adaptive_score"), 0)
        tradable_edge_delta = new["tradable_edge"] - _num(old.get("tradable_edge"), 0)
        fill_delta = new["fill_probability"] - _num(old.get("fill_probability"), 0)
        flow_delta = new["flow_score"] - _num(old.get("flow_score"), 0)

        if old.get("consensus_final_recommendation") != new["consensus_final_recommendation"]:
            events.append(self._event(
                "CONSENSUS_CHANGE",
                key,
                f"Consensus changed from {old.get('consensus_final_recommendation')} to {new['consensus_final_recommendation']}.",
                new,
                item,
                severity="HIGH",
            ))

        if old.get("execution_decision") != new["execution_decision"]:
            sev = "CRITICAL" if new["execution_decision"] == "EXECUTE" else "HIGH"
            events.append(self._event(
                "EXECUTION_DECISION_CHANGE",
                key,
                f"Execution decision changed from {old.get('execution_decision')} to {new['execution_decision']}.",
                new,
                item,
                severity=sev,
            ))

        if conf_delta >= 8:
            events.append(self._event(
                "CONFIDENCE_JUMP",
                key,
                f"Consensus confidence jumped +{conf_delta:.2f} points.",
                new,
                item,
                severity="HIGH",
            ))

        if adaptive_delta >= 7:
            events.append(self._event(
                "SCORE_JUMP",
                key,
                f"Adaptive score improved +{adaptive_delta:.2f} points.",
                new,
                item,
                severity="MEDIUM",
            ))

        if edge_delta <= -0.08:
            events.append(self._event(
                "EDGE_DECAY",
                key,
                f"Raw edge compressed {edge_delta:.4f}.",
                new,
                item,
                severity="MEDIUM",
            ))

        if tradable_edge_delta >= 0.05:
            events.append(self._event(
                "TRADABLE_EDGE_IMPROVEMENT",
                key,
                f"Tradable edge improved +{tradable_edge_delta:.4f}.",
                new,
                item,
                severity="HIGH",
            ))

        if fill_delta >= 8:
            events.append(self._event(
                "FILL_PROBABILITY_IMPROVEMENT",
                key,
                f"Fill probability improved +{fill_delta:.2f} points.",
                new,
                item,
                severity="MEDIUM",
            ))

        if old.get("tradability") != new["tradability"]:
            events.append(self._event(
                "TRADABILITY_CHANGE",
                key,
                f"Tradability changed from {old.get('tradability')} to {new['tradability']}.",
                new,
                item,
                severity="HIGH" if new["tradability"] in ("GOOD", "CAUTION") else "MEDIUM",
            ))

        if old.get("flow_signal") != new["flow_signal"]:
            events.append(self._event(
                "FLOW_SIGNAL_CHANGE",
                key,
                f"Order flow changed from {old.get('flow_signal')} to {new['flow_signal']}.",
                new,
                item,
                severity="HIGH" if new["flow_signal"] in ("BULLISH_FLOW", "IMPROVING_FLOW") else "MEDIUM",
            ))

        if flow_delta >= 15:
            events.append(self._event(
                "FLOW_SCORE_JUMP",
                key,
                f"Flow score improved +{flow_delta:.2f} points.",
                new,
                item,
                severity="MEDIUM",
            ))

        return events

    def _event(self, event_type, key, message, snap, item, severity="INFO"):
        return {
            "module": "oracle_live_opportunity_monitor",
            "version": self.version,
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "severity": severity,
            "key": key,
            "ticker": snap.get("ticker"),
            "title": snap.get("title"),
            "message": message,
            "snapshot": snap,
            "compact_card": self._event_card(event_type, severity, message, snap),
        }

    def _event_card(self, event_type, severity, message, snap):
        return "\n".join([
            "📡 ORACLE LIVE MONITOR",
            f"Event: {event_type}",
            f"Severity: {severity}",
            f"Ticker: {snap.get('ticker')}",
            f"Market: {snap.get('title')}",
            "",
            message,
            "",
            f"Consensus: {snap.get('consensus_final_recommendation')} | {snap.get('consensus_confidence')}%",
            f"Execution: {snap.get('execution_decision')}",
            f"Grade/Risk: {snap.get('grade')} / {snap.get('risk')}",
            f"Tradability: {snap.get('tradability')} | Micro {snap.get('microstructure_score')}",
            f"Order Book: {snap.get('order_book_rating')} | Fill {snap.get('fill_probability')}%",
            f"Flow: {snap.get('flow_signal')} | {snap.get('flow_score')}",
        ])

    def _status(self, new_events, status):
        counts = {}
        for e in self.state.get("events", []):
            t = e.get("event_type", "UNKNOWN")
            counts[t] = counts.get(t, 0) + 1

        return {
            "module": "oracle_live_opportunity_monitor",
            "version": self.version,
            "status": status,
            "tracked_opportunities": len(self.state.get("opportunities", {})),
            "new_events": len(new_events),
            "events": new_events,
            "event_counts": counts,
            "latest_events": self.state.get("events", [])[-10:],
            "state_file": str(STATE_FILE),
        }

    def diagnostics(self):
        return {
            "module": "oracle_live_opportunity_monitor",
            "version": self.version,
            "status": "ok",
            "tracked_opportunities": len(self.state.get("opportunities", {})),
            "events": len(self.state.get("events", [])),
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


oracle_live_opportunity_monitor = OracleLiveOpportunityMonitor()


if __name__ == "__main__":
    sample = [{
        "ticker": "TEST",
        "title": "Sample monitored opportunity",
        "grade": "B+",
        "risk": "MEDIUM",
        "edge": 0.12,
        "adaptive_score": 67,
        "consensus_final_recommendation": "WATCH",
        "consensus_confidence": 66,
        "execution_decision": "WATCH_ONLY",
        "tradability": "CAUTION",
        "microstructure_score": 64,
        "order_book_rating": "FAIR",
        "tradable_edge": 0.08,
        "fill_probability": 55,
        "flow_signal": "NEUTRAL_FLOW",
        "flow_score": 50,
    }]

    result = oracle_live_opportunity_monitor.observe(sample)
    print(json.dumps(result, indent=2))
