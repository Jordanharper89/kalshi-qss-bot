from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
ALERTS = ROOT / "oracle_smart_alert_prioritizer.py"
CONTINUOUS = ROOT / "oracle_continuous_intelligence.py"

ALERTS_CODE = r'''
"""
ORACLE-053 Smart Alert Prioritizer

Purpose:
- Convert Oracle monitor/lifecycle events into ranked actionable alerts.
- Suppress noisy BLOCKED/weak alerts.
- Highlight EXECUTION_READY, improving lifecycle, confidence jumps,
  tradability improvements, and strong order flow.
- Does NOT place trades.
"""

from datetime import datetime, UTC
from pathlib import Path
import json

STATE_FILE = Path("oracle_smart_alert_prioritizer_state.json")
MAX_ALERTS = 500


def _num(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _txt(v):
    return str(v or "").strip()


class OracleSmartAlertPrioritizer:
    def __init__(self):
        self.version = "ORACLE-053"
        self.state = {
            "alerts": [],
            "suppressed": [],
        }
        self._load()

    def prioritize(self, status_snapshot):
        ranked = []
        monitor_events = []

        if isinstance(status_snapshot, dict):
            ranked = status_snapshot.get("last_ranked") or []
            monitor_events = status_snapshot.get("live_monitor_events") or []

        if not isinstance(ranked, list):
            ranked = []
        if not isinstance(monitor_events, list):
            monitor_events = []

        alerts = []

        for item in ranked:
            if isinstance(item, dict):
                alert = self._score_opportunity(item)
                if alert:
                    alerts.append(alert)

        for event in monitor_events:
            if isinstance(event, dict):
                alert = self._score_event(event)
                if alert:
                    alerts.append(alert)

        deduped = self._dedupe(alerts)
        deduped.sort(key=lambda x: x.get("priority_score", 0), reverse=True)

        actionable = [a for a in deduped if not a.get("suppressed")]
        suppressed = [a for a in deduped if a.get("suppressed")]

        self.state["alerts"].extend(actionable)
        self.state["alerts"] = self.state["alerts"][-MAX_ALERTS:]

        self.state["suppressed"].extend(suppressed)
        self.state["suppressed"] = self.state["suppressed"][-MAX_ALERTS:]

        self._save()

        return {
            "module": "oracle_smart_alert_prioritizer",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "new_alerts": len(actionable),
            "suppressed": len(suppressed),
            "top_alerts": actionable[:10],
            "all_ranked_alerts": deduped[:25],
            "alert_counts": self._counts(actionable),
            "state_file": str(STATE_FILE),
        }

    def _score_opportunity(self, item):
        ticker = item.get("ticker")
        title = item.get("title")

        lifecycle_state = _txt(item.get("lifecycle_state"))
        lifecycle_score = _num(item.get("lifecycle_score"), 0)
        execution_decision = _txt(item.get("execution_decision"))
        consensus = _txt(item.get("consensus_final_recommendation"))
        consensus_conf = _num(item.get("consensus_confidence"), 0)
        grade = _txt(item.get("grade"))
        risk = _txt(item.get("risk"))
        tradability = _txt(item.get("tradability"))
        micro_score = _num(item.get("microstructure_score"), 0)
        order_book = _txt(item.get("order_book_rating"))
        fill_probability = _num(item.get("fill_probability"), 0)
        tradable_edge = _num(item.get("tradable_edge"), 0)
        flow_signal = _txt(item.get("flow_signal"))
        flow_score = _num(item.get("flow_score"), 0)

        score = 0
        reasons = []
        suppress = False

        if execution_decision == "EXECUTE":
            score += 80
            reasons.append("Gatekeeper says EXECUTE")

        elif execution_decision == "WATCH_ONLY":
            score += 35
            reasons.append("Gatekeeper says WATCH_ONLY")

        elif execution_decision == "REQUIRES_REVIEW":
            score += 45
            reasons.append("Gatekeeper requires review")

        elif execution_decision == "BLOCK":
            score -= 25
            reasons.append("Gatekeeper blocked")

        if lifecycle_state == "EXECUTION_READY":
            score += 60
            reasons.append("Lifecycle execution-ready")
        elif lifecycle_state == "IMPROVING":
            score += 35
            reasons.append("Lifecycle improving")
        elif lifecycle_state == "ACTIVE":
            score += 18
            reasons.append("Lifecycle active")
        elif lifecycle_state == "NEW":
            score += 8
            reasons.append("New tracked opportunity")
        elif lifecycle_state in ("BLOCKED", "STALE"):
            score -= 20
            reasons.append(f"Lifecycle {lifecycle_state}")

        if consensus in ("BUY YES", "BUY NO"):
            score += 35
            reasons.append(f"Directional consensus: {consensus}")
        elif consensus == "WATCH":
            score += 8
            reasons.append("Consensus watch")
        elif consensus == "PASS":
            score -= 20
            reasons.append("Consensus pass")

        if consensus_conf >= 80:
            score += 20
            reasons.append("High consensus confidence")
        elif consensus_conf >= 68:
            score += 10
            reasons.append("Moderate consensus confidence")
        elif consensus_conf < 55:
            score -= 12
            reasons.append("Low consensus confidence")

        if grade in ("A+", "A", "A-", "B+"):
            score += 15
            reasons.append(f"Strong grade: {grade}")
        elif grade == "PASS":
            score -= 20
            reasons.append("Grade PASS")

        if risk == "HIGH":
            score -= 25
            reasons.append("High risk")

        if tradability == "GOOD":
            score += 25
            reasons.append("Good tradability")
        elif tradability == "CAUTION":
            score += 8
            reasons.append("Caution tradability")
        elif tradability in ("POOR", "UNTRADABLE"):
            score -= 25
            reasons.append(f"Tradability {tradability}")

        if order_book == "GOOD":
            score += 20
            reasons.append("Good order book")
        elif order_book == "FAIR":
            score += 8
            reasons.append("Fair order book")
        elif order_book in ("WEAK", "UNUSABLE"):
            score -= 18
            reasons.append(f"Order book {order_book}")

        if fill_probability >= 65:
            score += 15
            reasons.append("Fill probability acceptable")
        elif fill_probability < 35:
            score -= 15
            reasons.append("Fill probability weak")

        if tradable_edge >= 0.10:
            score += 15
            reasons.append("Strong tradable edge")
        elif tradable_edge <= 0:
            score -= 20
            reasons.append("No tradable edge")

        if flow_signal in ("BULLISH_FLOW", "IMPROVING_FLOW"):
            score += 20
            reasons.append(f"Positive flow: {flow_signal}")
        elif flow_signal in ("DETERIORATING_FLOW", "AVOID_FLOW"):
            score -= 18
            reasons.append(f"Weak flow: {flow_signal}")

        if flow_score >= 75:
            score += 10
            reasons.append("Strong flow score")
        elif flow_score < 35:
            score -= 8
            reasons.append("Weak flow score")

        if execution_decision == "BLOCK" and lifecycle_state == "BLOCKED" and tradability in ("POOR", "UNTRADABLE"):
            suppress = True

        if score < 35:
            suppress = True

        priority = self._priority(score, suppress)

        return {
            "module": "oracle_smart_alert_prioritizer",
            "version": self.version,
            "timestamp": datetime.now(UTC).isoformat(),
            "source": "opportunity",
            "ticker": ticker,
            "title": title,
            "priority": priority,
            "priority_score": round(score, 2),
            "suppressed": suppress,
            "execution_decision": execution_decision,
            "lifecycle_state": lifecycle_state,
            "consensus": consensus,
            "consensus_confidence": consensus_conf,
            "tradability": tradability,
            "order_book_rating": order_book,
            "flow_signal": flow_signal,
            "reasons": reasons[:10],
            "compact_card": self._card(
                ticker, title, priority, score, suppress, execution_decision,
                lifecycle_state, consensus, consensus_conf, tradability,
                order_book, flow_signal, reasons
            ),
        }

    def _score_event(self, event):
        event_type = _txt(event.get("event_type"))
        severity = _txt(event.get("severity"))
        snap = event.get("snapshot") if isinstance(event.get("snapshot"), dict) else {}

        score = 25
        reasons = [event.get("message", event_type)]

        if severity == "CRITICAL":
            score += 55
        elif severity == "HIGH":
            score += 35
        elif severity == "MEDIUM":
            score += 18

        if event_type in ("EXECUTION_DECISION_CHANGE", "CONSENSUS_CHANGE"):
            score += 25
        elif event_type in ("CONFIDENCE_JUMP", "TRADABLE_EDGE_IMPROVEMENT"):
            score += 20
        elif event_type in ("FLOW_SIGNAL_CHANGE", "FILL_PROBABILITY_IMPROVEMENT"):
            score += 12
        elif event_type in ("EDGE_DECAY",):
            score -= 5

        execution = _txt(snap.get("execution_decision"))
        if execution == "EXECUTE":
            score += 35
        elif execution == "BLOCK":
            score -= 18

        tradability = _txt(snap.get("tradability"))
        if tradability in ("POOR", "UNTRADABLE"):
            score -= 15

        suppress = score < 35
        priority = self._priority(score, suppress)

        return {
            "module": "oracle_smart_alert_prioritizer",
            "version": self.version,
            "timestamp": datetime.now(UTC).isoformat(),
            "source": "monitor_event",
            "event_type": event_type,
            "severity": severity,
            "ticker": event.get("ticker"),
            "title": event.get("title"),
            "priority": priority,
            "priority_score": round(score, 2),
            "suppressed": suppress,
            "execution_decision": execution,
            "lifecycle_state": "",
            "consensus": snap.get("consensus_final_recommendation"),
            "consensus_confidence": snap.get("consensus_confidence"),
            "tradability": tradability,
            "order_book_rating": snap.get("order_book_rating"),
            "flow_signal": snap.get("flow_signal"),
            "reasons": reasons[:10],
            "compact_card": self._card(
                event.get("ticker"), event.get("title"), priority, score, suppress,
                execution, "", snap.get("consensus_final_recommendation"),
                snap.get("consensus_confidence"), tradability,
                snap.get("order_book_rating"), snap.get("flow_signal"), reasons
            ),
        }

    def _priority(self, score, suppress):
        if suppress:
            return "SUPPRESSED"
        if score >= 100:
            return "CRITICAL"
        if score >= 80:
            return "HIGH"
        if score >= 60:
            return "MEDIUM"
        return "LOW"

    def _dedupe(self, alerts):
        best = {}
        for a in alerts:
            key = f"{a.get('source')}|{a.get('ticker')}|{a.get('event_type','opportunity')}"
            if key not in best or a.get("priority_score", 0) > best[key].get("priority_score", 0):
                best[key] = a
        return list(best.values())

    def _counts(self, alerts):
        counts = {}
        for a in alerts:
            p = a.get("priority", "UNKNOWN")
            counts[p] = counts.get(p, 0) + 1
        return counts

    def _card(self, ticker, title, priority, score, suppress, execution, lifecycle, consensus, conf, tradability, order_book, flow, reasons):
        lines = [
            "🚨 ORACLE SMART ALERT",
            f"Priority: {priority}",
            f"Score: {round(float(score or 0), 2)}",
            f"Suppressed: {suppress}",
            f"Ticker: {ticker}",
            f"Market: {title}",
            "",
            f"Execution: {execution}",
            f"Lifecycle: {lifecycle}",
            f"Consensus: {consensus} | {conf}%",
            f"Tradability: {tradability}",
            f"Order Book: {order_book}",
            f"Flow: {flow}",
            "",
            "Reasons:",
        ]

        for r in reasons[:8]:
            lines.append(f"- {r}")

        return "\n".join(lines)

    def diagnostics(self):
        return {
            "module": "oracle_smart_alert_prioritizer",
            "version": self.version,
            "status": "ok",
            "stored_alerts": len(self.state.get("alerts", [])),
            "stored_suppressed": len(self.state.get("suppressed", [])),
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


oracle_smart_alert_prioritizer = OracleSmartAlertPrioritizer()


if __name__ == "__main__":
    sample = {
        "last_ranked": [{
            "ticker": "TEST",
            "title": "Sample alert opportunity",
            "grade": "A-",
            "risk": "MEDIUM",
            "edge": 0.12,
            "adaptive_score": 78,
            "consensus_final_recommendation": "BUY YES",
            "consensus_confidence": 82,
            "execution_decision": "WATCH_ONLY",
            "tradability": "CAUTION",
            "microstructure_score": 67,
            "order_book_rating": "FAIR",
            "tradable_edge": 0.08,
            "fill_probability": 55,
            "flow_signal": "IMPROVING_FLOW",
            "flow_score": 70,
            "lifecycle_state": "IMPROVING",
            "lifecycle_score": 76,
        }],
        "live_monitor_events": [],
    }

    import pprint
    pprint.pp(oracle_smart_alert_prioritizer.prioritize(sample))
'''

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-053 Smart Alert Prioritizer Integration
# ============================================================

try:
    from oracle_smart_alert_prioritizer import oracle_smart_alert_prioritizer
except Exception:
    oracle_smart_alert_prioritizer = None


def _oracle053_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            if oracle_smart_alert_prioritizer is None:
                _state["smart_alert_status"] = {"status": "missing"}
                _state["smart_alerts"] = []
                return

            snapshot = dict(_state)
            result = oracle_smart_alert_prioritizer.prioritize(snapshot)
            _state["smart_alert_status"] = result
            _state["smart_alerts"] = result.get("top_alerts", [])
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["smart_alert_status"] = {
                "status": "error",
                "error": str(exc),
            }
            _state["smart_alerts"] = []


if "_oracle053_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle053_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle053_original_run_cycle(*args, **kwargs)
        _oracle053_enrich_state()
        return result


if "_oracle053_original_status" not in globals() and "status" in globals():
    _oracle053_original_status = status

    def status(*args, **kwargs):
        result = _oracle053_original_status(*args, **kwargs)
        _oracle053_enrich_state()

        if isinstance(result, dict):
            result["smart_alert_status"] = (
                globals().get("_state", {}).get("smart_alert_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["smart_alerts"] = (
                globals().get("_state", {}).get("smart_alerts")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-053
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle053_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-053 INSTALLER")
    print(" Smart Alert Prioritizer")
    print("===================================")

    backup(ALERTS)
    ALERTS.write_text(ALERTS_CODE, encoding="utf-8")
    print("[OK] Created oracle_smart_alert_prioritizer.py")

    if not CONTINUOUS.exists():
        print("[WARN] oracle_continuous_intelligence.py not found; integration skipped")
    else:
        text = CONTINUOUS.read_text(encoding="utf-8", errors="ignore")
        if "ORACLE-053 Smart Alert Prioritizer Integration" in text:
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
    print(" python oracle_smart_alert_prioritizer.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('smart_alert_status')); print(s.get('smart_alerts')[:3])\"")
    print("")
    print("[DONE] ORACLE-053 Smart Alert Prioritizer installed")


if __name__ == "__main__":
    main()