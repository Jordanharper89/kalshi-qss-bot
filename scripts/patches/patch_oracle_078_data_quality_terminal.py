from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_data_quality_terminal.py")

CODE = r'''
"""
ORACLE-078 Data Quality Terminal

Purpose:
- Simple terminal view for ORACLE-077 Data Quality Planner.
- Does NOT place trades.

Commands:
 python oracle_data_quality_terminal.py
 python oracle_data_quality_terminal.py full
"""

import sys


def run(full=False):
    import oracle_continuous_intelligence as o

    o.run_cycle()
    s = o.status()

    dq = s.get("data_quality_planner_status") or {}

    print("")
    print("============================================================")
    print(" ORACLE DATA QUALITY TERMINAL")
    print("============================================================")
    print(dq.get("compact_card", "No data quality planner output available."))
    print("============================================================")

    if full:
        print("")
        print("REPAIR SCORES")
        print("------------------------------------------------------------")
        for k, v in (dq.get("repair_scores") or {}).items():
            print(f"{k}: {v}")

        print("")
        print("RECOMMENDATIONS")
        print("------------------------------------------------------------")
        for i, r in enumerate(dq.get("recommendations") or [], 1):
            print(f"{i}. [{r.get('priority')}] {r.get('area')} :: score={r.get('score')}")
            print(f"   {r.get('recommendation')}")

    print("")
    print("============================================================")
    print(" END ORACLE DATA QUALITY TERMINAL")
    print("============================================================")


def main():
    args = [a.lower().strip() for a in sys.argv[1:]]
    run(full=("full" in args))


if __name__ == "__main__":
    main()
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle078_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-078 INSTALLER")
    print(" Data Quality Terminal")
    print("===================================")

    b = backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")

    print("[OK] Created oracle_data_quality_terminal.py")
    if b:
        print(f"[OK] Backup created: {b}")

    print("")
    print("Tests:")
    print(" python oracle_data_quality_terminal.py")
    print(" python oracle_data_quality_terminal.py full")
    print("")
    print("[DONE] ORACLE-078 Data Quality Terminal installed")


if __name__ == "__main__":
    main()