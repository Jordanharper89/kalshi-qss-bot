
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
    "data": ["python", "oracle_data_quality_terminal.py"],
    "data_full": ["python", "oracle_data_quality_terminal.py", "full"],
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
    print(" python oracle_master_control.py data")
    print(" python oracle_master_control.py data full")
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

    if key == "data":
        if len(args) > 1 and args[1] == "full":
            run_cmd(COMMANDS["data_full"])
        else:
            run_cmd(COMMANDS["data"])
        return

    if key in COMMANDS:
        run_cmd(COMMANDS[key])
        return

    print(f"Unknown command: {key}")
    menu()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
