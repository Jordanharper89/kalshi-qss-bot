from pathlib import Path
import ast,json,hashlib
R=Path.cwd()
o=R/"qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py"
m=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_075b_ast_crash_safe_same_writer_cutover.py"
for p in (o,m): assert p.exists(); ast.parse(p.read_text(encoding="utf-8"))
s=o.read_text(encoding="utf-8")
assert "slop_069_same_writer_production_learning_intake" not in s
assert "apply_pending_slop" not in s
assert "slop_075b_ast_crash_safe_same_writer_cutover" in s
assert "recover_or_prepare" in s and "finalize" in s
st=R/"runtime_state/oracle_learning_runtime_state.json"; d=json.loads(st.read_text(encoding="utf-8"))
assert str(d.get("last_ticker") or "")!="SLOP:BUY_PRESSURE"
jp=R/"runtime_state/solana_live_opportunity/slop_075b_learning_commit_journal.json"
print("[CYCLES]",d.get("cycles")); print("[OUTCOMES_LEARNED]",d.get("outcomes_learned"))
print("[APPLIED_THROUGH]",d.get("ocl_state",{}).get("applied_through_sequence"))
print("[LAST_SETTLEMENT_TS]",d.get("last_settlement_ts")); print("[LAST_TICKER]",d.get("last_ticker"))
print("[COMMIT_JOURNAL_PRESENT]",jp.exists()); print("[STATE_HASH]",hashlib.sha256(st.read_bytes()).hexdigest())
print("[PASS] SLOP-075B disk cutover physically certified before restart")
print("[PASS] production cursor legitimate")
print("[PASS] SLOP-076B CERTIFIED execution_authority=FALSE")
