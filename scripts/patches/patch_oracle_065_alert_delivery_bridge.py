from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
TARGET = ROOT / "oracle_alert_delivery_bridge.py"
CONTINUOUS = ROOT / "oracle_continuous_intelligence.py"

CODE = r'''
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
'''

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-065 Alert Delivery Bridge Integration
# ============================================================

try:
    from oracle_alert_delivery_bridge import oracle_alert_delivery_bridge
except Exception:
    oracle_alert_delivery_bridge = None


def _oracle065_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            outbox = _state.get("alert_outbox", [])

            if oracle_alert_delivery_bridge is None:
                _state["alert_delivery_status"] = {"status": "missing"}
                _state["alert_delivery_payloads"] = []
                return

            result = oracle_alert_delivery_bridge.prepare(outbox if isinstance(outbox, list) else [])
            _state["alert_delivery_status"] = result
            _state["alert_delivery_payloads"] = result.get("payloads", [])
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["alert_delivery_status"] = {"status": "error", "error": str(exc)}
            _state["alert_delivery_payloads"] = []


if "_oracle065_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle065_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle065_original_run_cycle(*args, **kwargs)
        _oracle065_enrich_state()
        return result


if "_oracle065_original_status" not in globals() and "status" in globals():
    _oracle065_original_status = status

    def status(*args, **kwargs):
        result = _oracle065_original_status(*args, **kwargs)
        _oracle065_enrich_state()

        if isinstance(result, dict):
            result["alert_delivery_status"] = (
                globals().get("_state", {}).get("alert_delivery_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["alert_delivery_payloads"] = (
                globals().get("_state", {}).get("alert_delivery_payloads")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-065
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle065_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-065 INSTALLER")
    print(" Alert Delivery Bridge")
    print("===================================")

    backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")
    print("[OK] Created oracle_alert_delivery_bridge.py")

    if CONTINUOUS.exists():
        text = CONTINUOUS.read_text(encoding="utf-8", errors="ignore")
        if "ORACLE-065 Alert Delivery Bridge Integration" in text:
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
    else:
        print("[WARN] oracle_continuous_intelligence.py not found")

    print("")
    print("Tests:")
    print(" python oracle_alert_delivery_bridge.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('alert_delivery_status')); print(s.get('alert_delivery_payloads')[:3])\"")
    print("")
    print("[DONE] ORACLE-065 Alert Delivery Bridge installed")


if __name__ == "__main__":
    main()