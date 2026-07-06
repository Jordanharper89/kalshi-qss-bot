from pathlib import Path
from datetime import datetime
import json
import shutil

TARGET = Path("oracle_state_file_inspector.py")

CODE = r'''
"""
ORACLE-074 State File Inspector

Purpose:
- Inspect Oracle JSON state files.
- Detect missing, empty, oversized, or corrupt state files.
- Does NOT delete or modify state files.
"""

from pathlib import Path
from datetime import datetime, UTC
import json

STATE_FILES = [
    "oracle_execution_policy_config.json",
    "oracle_order_flow_state.json",
    "oracle_live_opportunity_monitor_state.json",
    "oracle_opportunity_lifecycle_state.json",
    "oracle_smart_alert_prioritizer_state.json",
    "oracle_portfolio_exposure_state.json",
    "oracle_execution_queue_state.json",
    "oracle_alert_outbox_state.json",
    "oracle_alert_delivery_bridge_state.json",
    "oracle_live_trade_tracker_state.json",
    "oracle_signal_learning_memory_state.json",
]


def inspect_file(path):
    p = Path(path)
    row = {
        "file": path,
        "exists": p.exists(),
        "size_bytes": 0,
        "json_ok": False,
        "top_keys": [],
        "counts": {},
        "status": "missing",
        "error": None,
    }

    if not p.exists():
        return row

    row["size_bytes"] = p.stat().st_size

    if row["size_bytes"] == 0:
        row["status"] = "empty"
        return row

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        row["json_ok"] = True
        row["status"] = "ok"

        if isinstance(data, dict):
            row["top_keys"] = list(data.keys())[:20]
            for k, v in data.items():
                if isinstance(v, (list, dict)):
                    row["counts"][k] = len(v)
        elif isinstance(data, list):
            row["counts"]["list_items"] = len(data)
    except Exception as exc:
        row["status"] = "corrupt_json"
        row["error"] = str(exc)

    if row["size_bytes"] > 5_000_000:
        row["status"] = "oversized"

    return row


def run():
    rows = [inspect_file(f) for f in STATE_FILES]

    ok = sum(1 for r in rows if r["status"] == "ok")
    missing = sum(1 for r in rows if r["status"] == "missing")
    bad = sum(1 for r in rows if r["status"] not in ("ok", "missing"))

    result = {
        "module": "oracle_state_file_inspector",
        "version": "ORACLE-074",
        "status": "ok" if bad == 0 else "degraded",
        "timestamp": datetime.now(UTC).isoformat(),
        "ok": ok,
        "missing": missing,
        "bad": bad,
        "rows": rows,
    }

    print("")
    print("============================================================")
    print(" ORACLE STATE FILE INSPECTOR")
    print("============================================================")
    print(f"Status: {result['status']}")
    print(f"OK: {ok} | Missing: {missing} | Bad: {bad}")
    print("============================================================")

    for r in rows:
        icon = "✅" if r["status"] == "ok" else ("⚪" if r["status"] == "missing" else "⚠️")
        print(f"{icon} {r['file']} :: {r['status']} :: {r['size_bytes']} bytes")
        if r.get("counts"):
            print(f"   counts: {r['counts']}")
        if r.get("error"):
            print(f"   error: {r['error']}")

    print("============================================================")
    print(" END ORACLE STATE FILE INSPECTOR")
    print("============================================================")

    return result


if __name__ == "__main__":
    run()
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle074_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-074 INSTALLER")
    print(" State File Inspector")
    print("===================================")

    b = backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")

    print("[OK] Created oracle_state_file_inspector.py")
    if b:
        print(f"[OK] Backup created: {b}")

    print("")
    print("Tests:")
    print(" python oracle_state_file_inspector.py")
    print("")
    print("[DONE] ORACLE-074 State File Inspector installed")


if __name__ == "__main__":
    main()