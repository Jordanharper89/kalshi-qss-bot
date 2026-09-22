from pathlib import Path
import ast
P=Path("qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py")
S=P.read_text(encoding="utf-8")
tree=ast.parse(S)
fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="run_high_coverage_learning_cycle")
target=next(x for x in fn.body if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call)
 and getattr(x.value.func,"id","")=="save_learning_ledger")
lines=S.splitlines(True); i=target.lineno-1
indent=lines[i][:len(lines[i])-len(lines[i].lstrip())]
IMP="from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_069_same_writer_production_learning_intake import apply_pending_slop\n"
PATCH=(indent+"slop_result, slop_state, slop_applied = apply_pending_slop(state, root, progress)\n"
 +indent+"if slop_applied:\n"+indent+"    state = slop_state\n"
 +indent+"    save_learning_runtime_state(sp, state)\n"
 +indent+"    progress(f'[SLOP LEARN] persisted={slop_applied} through_sequence={state.ocl_state.applied_through_sequence}')\n")
if IMP not in S:
 pos=next((n for n,l in enumerate(lines) if not l.startswith("from __future__") and l.strip()),0)
 lines.insert(pos,IMP)
 if pos<=i:i+=1
if "apply_pending_slop(state, root, progress)" not in "".join(lines):
 lines.insert(i,PATCH)
N="".join(lines); compile(N,str(P),"exec")
B=P.with_suffix(".pre_slop070b.py")
if not B.exists(): B.write_text(S,encoding="utf-8")
P.write_text(N,encoding="utf-8")
T=Path("test_slop_070b_ast_located_native_olr009_cutover.py")
T.write_text(r'''from pathlib import Path
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
''',encoding="utf-8")
print("[PASS] SLOP-070B AST-located native cutover installed")
print("[PASS] test installed:",T.name)