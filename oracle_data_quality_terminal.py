
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
