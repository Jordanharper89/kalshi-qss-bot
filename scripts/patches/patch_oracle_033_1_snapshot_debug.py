from pathlib import Path

engine = Path("oracle_research_engine.py")

if not engine.exists():
    print("[ERROR] oracle_research_engine.py not found")
    raise SystemExit

text = engine.read_text(encoding="utf-8")

backup = Path("oracle_research_engine.py.oracle0331_backup")
backup.write_text(text, encoding="utf-8")
print("[OK] Backup saved")

if "ORACLE-033.1 DEBUG" not in text:

    debug = '''

# =====================================================
# ORACLE-033.1 DEBUG
# =====================================================

def oracle_debug_snapshot():

    try:
        snap = oracle_research_engine.get_snapshot()

        print("\\n==============================")
        print("ORACLE SNAPSHOT")
        print("==============================")
        print("Status:", snap.get("status"))
        print("Markets:", snap.get("markets_checked"))
        print("Provider Results:", len(snap.get("provider_results", [])))
        print("Ranked Opportunities:", len(snap.get("opportunities", [])))

        for i, opp in enumerate(snap.get("opportunities", [])[:10], start=1):
            print(
                f"{i}. "
                f"{opp.get('ticker')} | "
                f"{opp.get('oracle_score')} | "
                f"{opp.get('grade')}"
            )

        print("==============================\\n")

    except Exception as e:
        print("[ORACLE DEBUG]", e)

'''

    text += debug

engine.write_text(text, encoding="utf-8")

print("[DONE] ORACLE-033.1 Debug installed")