from pathlib import Path
import textwrap

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "historical_outcome_tracking_engine.py"
TEST_FILE = ROOT / "test_oi_030_historical_outcome_tracking_engine.py"

if not ENGINE.exists():
    raise FileNotFoundError("Missing OI-030 engine file. Install OI-030 first.")

text = ENGINE.read_text(encoding="utf-8")

if "def _std(values: List[float])" not in text:
    marker = "def _stats(values: List[float]) -> Dict[str, Any]:"
    insert_after = "    }\n\n"
    idx = text.find(insert_after, text.find(marker))
    if idx == -1:
        raise RuntimeError("Could not locate _stats function insertion point.")

    idx += len(insert_after)

    helper = textwrap.dedent("""
    def _std(values: List[float]) -> float:
        clean = [_safe_float(v) for v in values if v is not None]
        if len(clean) <= 1:
            return 0.0
        return round(pstdev(clean), 6)


    """)

    text = text[:idx] + helper + text[idx:]

ENGINE.write_text(text, encoding="utf-8")

print("========================================")
print(" OI-030.1 INSTALLER")
print(" Historical Outcome Tracking Hardening")
print("========================================")
print(f"[OK] Patched {ENGINE}")
print("")
print("[DONE] OI-030.1 installed")
print("")
print("Verify:")
print("python -c \"import qseries_v2.oracle_intelligence.historical_outcome_tracking_engine as m; print(hasattr(m,'_std'))\"")
print("")
print("Run:")
print("python test_oi_030_historical_outcome_tracking_engine.py")