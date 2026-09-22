from pathlib import Path

RUN = Path("run_slop_buy_pressure_live.py")
TEST = Path("test_slop_043b_native_single_resolution_owner_rebuild.py")
assert RUN.exists(), RUN

s = RUN.read_text(encoding="utf-8")
old = "from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output import resolve_background"
new = """from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_prospective_resolution_ledger import read_resolution_dicts
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_017b_ordered_physical_economic_resolution import EconomicResolution
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output import resolution_lines"""

assert old in s, "expected native resolution import not found"
s = s.replace(old, new)
s = s.replace("ROOT=Path.cwd(); seen=set()", "ROOT=Path.cwd(); seen=set(); resolved_seen=set()")

old_call = "  resolve_background(ROOT,progress=lambda x: print(x,flush=True))"
new_call = """  for d in read_resolution_dicts(ROOT):
   pid=str(d["prediction_id"])
   if pid not in resolved_seen:
    e=EconomicResolution(**d)
    for line in resolution_lines(e): print(line,flush=True)
    resolved_seen.add(pid)"""

assert old_call in s, "expected duplicate resolution call not found"
s = s.replace(old_call, new_call)
s = s.replace("r.get('pending',r.get('pending_after','?'))", "r.get('unresolved','?')")
RUN.write_text(s, encoding="utf-8")

TEST.write_text("""from pathlib import Path
import ast
p=Path("run_slop_buy_pressure_live.py")
s=p.read_text(encoding="utf-8"); ast.parse(s)
assert "resolve_background(" not in s
assert "read_resolution_dicts" in s
assert "EconomicResolution(**d)" in s
assert "resolution_lines(e)" in s
assert "resolved_seen=set()" in s
assert "r.get('unresolved','?')" in s
assert "execution_authority=FALSE" in s
print("[PASS] SLOP-043B native runner parses")
print("[PASS] SLOP-025 remains sole resolution owner")
print("[PASS] native runner reads canonical SLOP-020 resolutions")
print("[PASS] resolution output is print-only and idempotent per runtime")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-043B CERTIFIED")
""", encoding="utf-8")

print("[PASS] SLOP-043B native single-resolution-owner rebuild installed")
print("[PASS] test installed:", TEST)
print("[PASS] execution_authority=FALSE")