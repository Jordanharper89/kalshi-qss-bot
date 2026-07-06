from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
TARGET = ROOT / "oracle_alert_outbox_manager.py"
CONTINUOUS = ROOT / "oracle_continuous_intelligence.py"

CODE = r'''
"""
ORACLE-064 Alert Outbox Manager

Purpose:
- Stage final Oracle alerts into a persistent outbox.
- Dedupe repeated alerts.
- Track status: NEW, QUEUED, SUPPRESSED.
- Does NOT send Telegram messages.
- Does NOT place trades.
"""

from datetime import datetime, UTC
from pathlib import Path
import hashlib
import json

STATE_FILE = Path("oracle_alert_outbox_state.json")
MAX_OUTBOX = 500


class OracleAlertOutboxManager:
    def __init__(self):
        self.version = "ORACLE-064"
        self.state = {
            "outbox": [],
            "suppressed": [],
            "seen_keys": {},
        }
        self._load()

    def stage_alerts(self, alerts):
        alerts = alerts if isinstance(alerts, list) else []

        staged = []
        suppressed = []

        for alert in alerts:
            if not isinstance(alert, dict):
                continue

            item = self._normalize(alert)
            key = item["alert_key"]

            prior = self.state["seen_keys"].get(key)

            if prior:
                item["outbox_status"] = "SUPPRESSED"
                item["suppression_reason"] = "Duplicate alert already staged"
                suppressed.append(item)
                continue

            if item["final_action"] == "NO_TRADE":
                item["outbox_status"] = "SUPPRESSED"
                item["suppression_reason"] = "NO_TRADE alert suppressed from active outbox"
                suppressed.append(item)
                self.state["seen_keys"][key] = item["created_at"]
                continue

            item["outbox_status"] = "QUEUED"
            item["suppression_reason"] = None
            staged.append(item)
            self.state["seen_keys"][key] = item["created_at"]

        self.state["outbox"].extend(staged)
        self.state["outbox"] = self.state["outbox"][-MAX_OUTBOX:]

        self.state["suppressed"].extend(suppressed)
        self.state["suppressed"] = self.state["suppressed"][-MAX_OUTBOX:]

        self._save()

        return {
            "module": "oracle_alert_outbox_manager",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "new_queued": len(staged),
            "new_suppressed": len(suppressed),
            "queued_total": len(self.state["outbox"]),
            "suppressed_total": len(self.state["suppressed"]),
            "queued": staged,
            "suppressed": suppressed[:10],
            "outbox": self.state["outbox"][-25:],
            "state_file": str(STATE_FILE),
        }

    def _normalize(self, alert):
        ticker = alert.get("ticker", "UNKNOWN")
        action = alert.get("final_action", "NO_TRADE")
        score = alert.get("final_score", 0)
        card = alert.get("alert_card", "")

        key_raw = f"{ticker}|{action}|{score}|{card[:120]}"
        key = hashlib.sha1(key_raw.encode("utf-8", errors="ignore")).hexdigest()[:18]

        priority = "LOW"
        if action == "READY_FOR_EXECUTION":
            priority = "CRITICAL"
        elif action == "HUMAN_REVIEW":
            priority = "HIGH"
        elif action == "WATCH":
            priority = "MEDIUM"

        return {
            "module": "oracle_alert_outbox_manager",
            "version": self.version,
            "alert_key": key,
            "created_at": datetime.now(UTC).isoformat(),
            "ticker": ticker,
            "title": alert.get("title"),
            "final_action": action,
            "final_score": score,
            "priority": priority,
            "telegram_ready": bool(alert.get("telegram_ready")),
            "q_series_ready": bool(alert.get("q_series_ready")),
            "alert_card": card,
        }

    def diagnostics(self):
        return {
            "module": "oracle_alert_outbox_manager",
            "version": self.version,
            "status": "ok",
            "queued_total": len(self.state.get("outbox", [])),
            "suppressed_total": len(self.state.get("suppressed", [])),
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


oracle_alert_outbox_manager = OracleAlertOutboxManager()


if __name__ == "__main__":
    sample = [{
        "ticker": "TEST",
        "title": "Sample alert",
        "final_action": "HUMAN_REVIEW",
        "final_score": 72,
        "telegram_ready": True,
        "q_series_ready": True,
        "alert_card": "🟡 ORACLE REVIEW\nTicker: TEST\nMarket: Sample alert",
    }]

    import pprint
    pprint.pp(oracle_alert_outbox_manager.stage_alerts(sample))
'''

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-064 Alert Outbox Manager Integration
# ============================================================

try:
    from oracle_alert_outbox_manager import oracle_alert_outbox_manager
except Exception:
    oracle_alert_outbox_manager = None


def _oracle064_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            alerts = _state.get("final_alerts", [])

            if oracle_alert_outbox_manager is None:
                _state["alert_outbox_status"] = {"status": "missing"}
                _state["alert_outbox"] = []
                return

            result = oracle_alert_outbox_manager.stage_alerts(alerts if isinstance(alerts, list) else [])
            _state["alert_outbox_status"] = result
            _state["alert_outbox"] = result.get("outbox", [])
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["alert_outbox_status"] = {"status": "error", "error": str(exc)}
            _state["alert_outbox"] = []


if "_oracle064_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle064_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle064_original_run_cycle(*args, **kwargs)
        _oracle064_enrich_state()
        return result


if "_oracle064_original_status" not in globals() and "status" in globals():
    _oracle064_original_status = status

    def status(*args, **kwargs):
        result = _oracle064_original_status(*args, **kwargs)
        _oracle064_enrich_state()

        if isinstance(result, dict):
            result["alert_outbox_status"] = (
                globals().get("_state", {}).get("alert_outbox_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["alert_outbox"] = (
                globals().get("_state", {}).get("alert_outbox")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-064
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle064_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-064 INSTALLER")
    print(" Alert Outbox Manager")
    print("===================================")

    backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")
    print("[OK] Created oracle_alert_outbox_manager.py")

    if CONTINUOUS.exists():
        text = CONTINUOUS.read_text(encoding="utf-8", errors="ignore")
        if "ORACLE-064 Alert Outbox Manager Integration" in text:
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
    print(" python oracle_alert_outbox_manager.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('alert_outbox_status')); print(s.get('alert_outbox')[:3])\"")
    print("")
    print("[DONE] ORACLE-064 Alert Outbox Manager installed")


if __name__ == "__main__":
    main()