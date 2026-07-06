from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_state_maintenance.py")

CODE = r'''
"""
ORACLE-075 State Maintenance Utility

Purpose:
- Backup or reset Oracle JSON state files safely.
- Does NOT modify code files.
- Does NOT place trades.

Commands:
 python oracle_state_maintenance.py status
 python oracle_state_maintenance.py backup
 python oracle_state_maintenance.py reset outbox
 python oracle_state_maintenance.py reset learning
 python oracle_state_maintenance.py reset tracker
 python oracle_state_maintenance.py reset all
"""

from pathlib import Path
from datetime import datetime
import json
import shutil
import sys

STATE_GROUPS = {
    "policy": ["oracle_execution_policy_config.json"],
    "outbox": [
        "oracle_alert_outbox_state.json",
        "oracle_alert_delivery_bridge_state.json",
        "oracle_smart_alert_prioritizer_state.json",
    ],
    "tracker": [
        "oracle_live_trade_tracker_state.json",
        "oracle_order_flow_state.json",
        "oracle_live_opportunity_monitor_state.json",
        "oracle_opportunity_lifecycle_state.json",
    ],
    "learning": [
        "oracle_signal_learning_memory_state.json",
    ],
    "portfolio": [
        "oracle_portfolio_exposure_state.json",
        "oracle_execution_queue_state.json",
    ],
}

ALL_FILES = sorted({f for files in STATE_GROUPS.values() for f in files})


def backup_files(files):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = Path(f"oracle_state_backup_{stamp}")
    folder.mkdir(exist_ok=True)

    copied = []
    missing = []

    for f in files:
        p = Path(f)
        if p.exists():
            shutil.copy2(p, folder / p.name)
            copied.append(f)
        else:
            missing.append(f)

    return folder, copied, missing


def reset_files(files):
    folder, copied, missing = backup_files(files)
    reset = []

    for f in files:
        p = Path(f)
        if p.exists():
            p.unlink()
            reset.append(f)

    return folder, reset, missing


def status():
    rows = []
    for f in ALL_FILES:
        p = Path(f)
        rows.append({
            "file": f,
            "exists": p.exists(),
            "size_bytes": p.stat().st_size if p.exists() else 0,
        })
    return rows


def print_status():
    print("")
    print("============================================================")
    print(" ORACLE STATE MAINTENANCE")
    print("============================================================")
    for r in status():
        icon = "✅" if r["exists"] else "⚪"
        print(f"{icon} {r['file']} :: {r['size_bytes']} bytes")
    print("============================================================")


def main():
    args = [a.lower().strip() for a in sys.argv[1:]]

    if not args or args[0] == "status":
        print_status()
        return

    if args[0] == "backup":
        folder, copied, missing = backup_files(ALL_FILES)
        print(f"[OK] Backup folder created: {folder}")
        print(f"[OK] Copied: {len(copied)}")
        print(f"[INFO] Missing: {len(missing)}")
        return

    if args[0] == "reset":
        if len(args) < 2:
            print("Missing reset group. Use: outbox, learning, tracker, portfolio, policy, all")
            raise SystemExit(1)

        group = args[1]
        if group == "all":
            files = ALL_FILES
        elif group in STATE_GROUPS:
            files = STATE_GROUPS[group]
        else:
            print(f"Unknown group: {group}")
            print(f"Valid groups: {list(STATE_GROUPS.keys()) + ['all']}")
            raise SystemExit(1)

        folder, reset, missing = reset_files(files)
        print(f"[OK] Backup folder created before reset: {folder}")
        print(f"[OK] Reset files: {reset}")
        print(f"[INFO] Missing files: {missing}")
        return

    print("Unknown command.")
    print(__doc__)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle075_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-075 INSTALLER")
    print(" State Maintenance Utility")
    print("===================================")

    b = backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")

    print("[OK] Created oracle_state_maintenance.py")
    if b:
        print(f"[OK] Backup created: {b}")

    print("")
    print("Tests:")
    print(" python oracle_state_maintenance.py status")
    print(" python oracle_state_maintenance.py backup")
    print("")
    print("Useful later:")
    print(" python oracle_state_maintenance.py reset outbox")
    print(" python oracle_state_maintenance.py reset learning")
    print(" python oracle_state_maintenance.py reset tracker")
    print("")
    print("[DONE] ORACLE-075 State Maintenance Utility installed")


if __name__ == "__main__":
    main()