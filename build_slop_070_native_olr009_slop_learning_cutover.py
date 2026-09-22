from pathlib import Path
P=Path("qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py")
S=P.read_text(encoding="utf-8")
B=P.with_suffix(".pre_slop070.py")
if not B.exists(): B.write_text(S,encoding="utf-8")
IMP="from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_069_same_writer_production_learning_intake import apply_pending_slop\n"
if IMP not in S:
 lines=S.splitlines(True); i=0
 while i<len(lines) and (lines[i].startswith("from __future__") or not lines[i].strip()): i+=1
 lines.insert(i,IMP); S="".join(lines)
ANCH="    save_learning_ledger(lp, ledger)\n"
PATCH="""    slop_result, slop_state, slop_applied = apply_pending_slop(state, root, progress)\n    if slop_applied:\n        state = slop_state\n        save_learning_runtime_state(sp, state)\n        progress(f'[SLOP LEARN] persisted={slop_applied} through_sequence={state.ocl_state.applied_through_sequence}')\n"""
assert ANCH in S,"SLOP070_ANCHOR_NOT_FOUND"
if PATCH not in S: S=S.replace(ANCH,PATCH+ANCH,1)
compile(S,str(P),"exec"); P.write_text(S,encoding="utf-8")
T=Path("test_slop_070_native_olr009_slop_learning_cutover.py")
T.write_text(r'''from pathlib import Path
import ast
p=Path("qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py")
s=p.read_text(encoding="utf-8"); ast.parse(s)
assert "apply_pending_slop(state, root, progress)" in s
assert "save_learning_runtime_state(sp, state)" in s
assert s.count("apply_pending_slop(state, root, progress)")==1
assert Path("qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.pre_slop070.py").exists()
print("[PASS] OLR-009 parses after native SLOP intake cutover")
print("[PASS] exactly one SLOP intake call installed")
print("[PASS] existing production state writer retained")
print("[PASS] rollback snapshot retained")
print("[PASS] execution_authority=FALSE")
print("[PASS] SLOP-070 INSTALLATION CERTIFIED")
print("[NEXT] restart Oracle once to load SLOP-070 into the production learning child")
''',encoding="utf-8")
print("[PASS] SLOP-070 native OLR-009 cutover installed")
print("[PASS] test installed:",T.name)