from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "oracle_intelligence" / "historical_outcome_tracking_engine.py"

code = TARGET.read_text(encoding="utf-8")

if "oracle_outcome_engine =" not in code:
    code = code.replace(
        "oracle_historical_outcome_tracking_engine = create_historical_outcome_tracking_engine\n",
        "oracle_historical_outcome_tracking_engine = create_historical_outcome_tracking_engine\n"
        "oracle_outcome_engine = create_historical_outcome_tracking_engine\n"
    )

if '"oracle_outcome_engine",' not in code:
    code = code.replace(
        '    "oracle_historical_outcome_tracking_engine",\n',
        '    "oracle_historical_outcome_tracking_engine",\n'
        '    "oracle_outcome_engine",\n'
    )

TARGET.write_text(code, encoding="utf-8")

print("========================================")
print(" OPS-014.1 PATCH")
print(" Historical Outcome Tracking Export Fix")
print("========================================")
print(f"[OK] Patched {TARGET}")
print("")
print("[DONE] OPS-014.1 installed")
print("")
print("Run:")
print("py test_ops_014_historical_outcome_tracking_runtime_path_migration.py")