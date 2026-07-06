from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_mode_switch.py")

CODE = r'''
"""
ORACLE-047.3 Execution Mode Switch

Easy command wrapper for Oracle execution policy.

Commands:
 python oracle_mode_switch.py status
 python oracle_mode_switch.py paper
 python oracle_mode_switch.py aggressive
 python oracle_mode_switch.py normal
 python oracle_mode_switch.py conservative
"""

import sys
import json
from oracle_execution_policy import oracle_execution_policy


ALIASES = {
    "paper": "PAPER",
    "sim": "PAPER",
    "simulation": "PAPER",
    "aggressive": "AGGRESSIVE",
    "agg": "AGGRESSIVE",
    "normal": "NORMAL",
    "prod": "NORMAL",
    "production": "NORMAL",
    "conservative": "CONSERVATIVE",
    "safe": "CONSERVATIVE",
    "strict": "CONSERVATIVE",
}


def print_status():
    d = oracle_execution_policy.diagnostics()
    print("")
    print("🧠 ORACLE EXECUTION MODE")
    print("=======================")
    print(f"Active Mode: {d.get('active_profile')}")
    print(f"Config File: {d.get('config_file')}")
    print(f"Config Exists: {d.get('config_exists')}")
    print("")
    print("Available:")
    for p in d.get("available_profiles", []):
        desc = d.get("profiles", {}).get(p, {}).get("description", "")
        print(f"- {p}: {desc}")
    print("")


def set_mode(name):
    key = str(name or "").lower().strip()
    if key not in ALIASES:
        print(f"Unknown mode: {name}")
        print("Use: paper, aggressive, normal, conservative, or status")
        raise SystemExit(1)

    profile = ALIASES[key]
    policy = oracle_execution_policy.set_profile(profile)

    print("")
    print("✅ ORACLE MODE SWITCHED")
    print("======================")
    print(f"Active Mode: {policy.get('profile')}")
    print(f"Description: {policy.get('description')}")
    print("")
    print("Thresholds:")
    print(f"- Execute Confidence: {policy.get('min_execute_confidence')}")
    print(f"- Execute Adaptive Score: {policy.get('min_execute_adaptive_score')}")
    print(f"- Watch Confidence: {policy.get('min_watch_confidence')}")
    print(f"- Allow PASS Grade: {policy.get('allow_pass_grade')}")
    print(f"- Requires Strong Consensus: {policy.get('requires_strong_consensus')}")
    print("")


def main():
    args = sys.argv[1:]

    if not args or args[0].lower() in ("status", "show"):
        print_status()
        return

    set_mode(args[0])


if __name__ == "__main__":
    main()
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle047_3_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-047.3 INSTALLER")
    print(" Execution Mode Switch")
    print("===================================")

    b = backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")

    print("[OK] Created oracle_mode_switch.py")
    if b:
        print(f"[OK] Backup created: {b}")

    print("")
    print("Tests:")
    print(" python oracle_mode_switch.py status")
    print(" python oracle_mode_switch.py paper")
    print(" python oracle_mode_switch.py normal")
    print("")
    print("[DONE] ORACLE-047.3 Execution Mode Switch installed")


if __name__ == "__main__":
    main()