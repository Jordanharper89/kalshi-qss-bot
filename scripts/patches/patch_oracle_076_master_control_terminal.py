from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_master_control.py")

CODE = r'''
"""
ORACLE-076 Master Control Terminal

Purpose:
- One command hub for Oracle control/diagnostics.
- Does NOT place trades.

Commands:
 python oracle_master_control.py menu
 python oracle_master_control.py final
 python oracle_master_control.py final full
 python oracle_master_control.py learning
 python oracle_master_control.py health
 python oracle_master_control.py doctor
 python oracle_master_control.py state
 python oracle_master_control.py backup
"""

import sys
import subprocess


COMMANDS = {
    "final": ["python", "oracle_final_terminal.py"],
    "final_full": ["python", "oracle_final_terminal.py", "5", "full"],
    "learning": ["python", "oracle_learning_terminal.py"],
    "health": ["python", "oracle_system_health.py"],
    "doctor": ["python", "oracle_pipeline_doctor.py"],
    "state": ["python", "oracle_state_file_inspector.py"],
    "backup": ["python", "oracle_state_maintenance.py", "backup"],
    "state_status": ["python", "oracle_state_maintenance.py", "status"],
}


def run_cmd(cmd):
    print("")
    print("============================================================")
    print("RUNNING:", " ".join(cmd))
    print("============================================================")
    subprocess.run(cmd)


def menu():
    print("")
    print("============================================================")
    print(" ORACLE MASTER CONTROL")
    print("============================================================")
    print("Commands:")
    print(" python oracle_master_control.py final")
    print(" python oracle_master_control.py final full")
    print(" python oracle_master_control.py learning")
    print(" python oracle_master_control.py health")
    print(" python oracle_master_control.py doctor")
    print(" python oracle_master_control.py state")
    print(" python oracle_master_control.py backup")
    print("============================================================")


def main():
    args = [a.lower().strip() for a in sys.argv[1:]]

    if not args or args[0] in ("menu", "help"):
        menu()
        return

    if args[0] == "final":
        if len(args) > 1 and args[1] == "full":
            run_cmd(COMMANDS["final_full"])
        else:
            run_cmd(COMMANDS["final"])
        return

    key = args[0]

    if key in COMMANDS:
        run_cmd(COMMANDS[key])
        return

    print(f"Unknown command: {key}")
    menu()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle076_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-076 INSTALLER")
    print(" Master Control Terminal")
    print("===================================")

    b = backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")

    print("[OK] Created oracle_master_control.py")
    if b:
        print(f"[OK] Backup created: {b}")

    print("")
    print("Tests:")
    print(" python oracle_master_control.py menu")
    print(" python oracle_master_control.py final")
    print(" python oracle_master_control.py doctor")
    print("")
    print("[DONE] ORACLE-076 Master Control Terminal installed")


if __name__ == "__main__":
    main()