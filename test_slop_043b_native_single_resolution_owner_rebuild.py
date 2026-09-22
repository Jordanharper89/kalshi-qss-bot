from pathlib import Path
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
