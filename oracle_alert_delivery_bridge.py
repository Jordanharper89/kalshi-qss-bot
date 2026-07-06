
"""
ORACLE-065 Alert Delivery Bridge

Purpose:
- Convert Oracle alert outbox into delivery-ready payloads.
- Supports Telegram-ready and Q Series-ready routing metadata.
- Does NOT send messages.
- Does NOT place trades.
"""

from datetime import datetime, UTC
from pathlib import Path
import json

STATE_FILE = Path("oracle_alert_delivery_bridge_state.json")


class OracleAlertDeliveryBridge:
    def __init__(self):
        self.version = "ORACLE-065"
        self.state = {
            "delivery_payloads": [],
            "history": [],
        }
        self._load()

    def prepare(self, outbox):
        outbox = outbox if isinstance(outbox, list) else []

        payloads = []

        for alert in outbox:
            if not isinstance(alert, dict):
                continue

            payload = self._payload(alert)
            payloads.append(payload)

        self.state["delivery_payloads"] = payloads[-100:]
        self.state["history"].append({
            "timestamp": datetime.now(UTC).isoformat(),
            "prepared": len(payloads),
            "telegram_ready": sum(1 for p in payloads if p.get("telegram_ready")),
            "q_series_ready": sum(1 for p in payloads if p.get("q_series_ready")),
        })
        self.state["history"] = self.state["history"][-200:]
        self._save()

        return {
            "module": "oracle_alert_delivery_bridge",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "prepared": len(payloads),
            "telegram_ready": sum(1 for p in payloads if p.get("telegram_ready")),
            "q_series_ready": sum(1 for p in payloads if p.get("q_series_ready")),
            "payloads": payloads,
            "state_file": str(STATE_FILE),
        }

    def _payload(self, alert):
        action = str(alert.get("final_action") or "NO_TRADE").upper()

        route = "SUPPRESSED"
        if action == "READY_FOR_EXECUTION":
            route = "Q_SERIES_REVIEW"
        elif action == "HUMAN_REVIEW":
            route = "TELEGRAM_REVIEW"
        elif action == "WATCH":
            route = "TELEGRAM_WATCH"

        return {
            "module": "oracle_alert_delivery_bridge",
            "version": self.version,
            "created_at": datetime.now(UTC).isoformat(),
            "alert_key": alert.get("alert_key"),
            "ticker": alert.get("ticker"),
            "title": alert.get("title"),
            "final_action": action,
            "final_score": alert.get("final_score"),
            "priority": alert.get("priority"),
            "route": route,
            "telegram_ready": bool(alert.get("telegram_ready")) and route in ("TELEGRAM_REVIEW", "TELEGRAM_WATCH", "Q_SERIES_REVIEW"),
            "q_series_ready": bool(alert.get("q_series_ready")) and route == "Q_SERIES_REVIEW",
            "message_text": alert.get("alert_card", ""),
            "send_status": "PENDING_MANUAL_REVIEW",
        }

    def diagnostics(self):
        return {
            "module": "oracle_alert_delivery_bridge",
            "version": self.version,
            "status": "ok",
            "payloads": len(self.state.get("delivery_payloads", [])),
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


oracle_alert_delivery_bridge = OracleAlertDeliveryBridge()


if __name__ == "__main__":
    sample = [{
        "alert_key": "abc123",
        "ticker": "TEST",
        "title": "Sample delivery alert",
        "final_action": "HUMAN_REVIEW",
        "final_score": 72,
        "priority": "HIGH",
        "telegram_ready": True,
        "q_series_ready": True,
        "alert_card": "🟡 ORACLE REVIEW\nTicker: TEST\nMarket: Sample delivery alert",
    }]

    import pprint
    pprint.pp(oracle_alert_delivery_bridge.prepare(sample))
