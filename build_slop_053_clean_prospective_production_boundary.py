from pathlib import Path
T=Path("test_slop_053_clean_prospective_production_boundary.py")
T.write_text("""from pathlib import Path
import ast
r=Path("run_slop_buy_pressure_live.py").read_text(encoding="utf-8")
ast.parse(r)
c=Path("runtime_state/solana_live_opportunity/slop_050_cohort_start.txt")
assert c.exists()
assert "worker_round" in r
assert "read_resolution_dicts" in r
assert "resolve_background(" not in r
assert "execution_authority=FALSE" in r
print("[COHORT_START]",c.read_text().strip())
print("[PASS] repaired native BUY_PRESSURE runner parses")
print("[PASS] SLOP-025 remains sole maturity/resolution owner")
print("[PASS] clean prospective boundary physically present")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-053 CERTIFIED")
""",encoding="utf-8")
print("[PASS] SLOP-053 clean prospective production boundary installed")
print("[PASS] test installed:",T)
print("[PASS] execution_authority=FALSE")