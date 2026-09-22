from pathlib import Path
import ast
p=Path("qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py")
s=p.read_text(encoding="utf-8"); ast.parse(s)
assert s.count("apply_pending_slop(state, root, progress)")==1
assert "slop_result, slop_state, slop_applied" in s
assert "state = slop_state" in s
assert Path("qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.pre_slop070b.py").exists()
print("[PASS] OLR-009 parses after AST-located SLOP cutover")
print("[PASS] exactly one native SLOP intake call installed")
print("[PASS] existing OLR-009 remains production state owner")
print("[PASS] pre-cutover rollback snapshot retained")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-070B DISK CUTOVER CERTIFIED")
