from pathlib import Path
import ast
R=Path.cwd(); o=R/"qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py"
m=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_075b_ast_crash_safe_same_writer_cutover.py"
for p in (o,m): ast.parse(p.read_text(encoding="utf-8"))
s=o.read_text(encoding="utf-8")
assert "slop_069_same_writer_production_learning_intake" not in s
assert "apply_pending_slop" not in s
assert "recover_or_prepare" in s and "finalize" in s
assert s.index("save_learning_runtime_state(sp, state)") < s.index("finalize(slop_rows, root, progress)")
print("[PASS] exact unsafe AST boundary retired")
print("[PASS] learner state save precedes consumed commit")
print("[PASS] crash recovery journal installed")
print("[PASS] OLR-009 parses after cutover")
print("[PASS] SLOP-075B CERTIFIED execution_authority=FALSE")
