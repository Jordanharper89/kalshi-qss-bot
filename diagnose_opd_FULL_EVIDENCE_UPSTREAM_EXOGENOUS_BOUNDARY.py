from pathlib import Path
import ast

ROOT=Path.cwd().resolve()
P=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"

src=P.read_text(encoding="utf-8")
tree=ast.parse(src)

targets={
    "materialize_current_states",
    "_run_single_contract",
    "_score_state_preprospective",
    "_freeze_predictions",
}

print("="*110)
print(" FULL-EVIDENCE UPSTREAM / FREEZE BOUNDARY DIAGNOSTIC")
print("="*110)
print("[FILE]",P)

for node in tree.body:
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in targets:
        print()
        print("="*110)
        print("[FUNCTION]",node.name,"LINES",node.lineno,"-",node.end_lineno)
        print("="*110)
        segment="\n".join(src.splitlines()[node.lineno-1:node.end_lineno])
        print(segment)

print()
print("="*110)
print("[IMPORTS / ASSEMBLY REFERENCES]")
print("="*110)

for i,line in enumerate(src.splitlines(),1):
    low=line.lower()
    if any(x in low for x in (
        "opd_042",
        "opd_062",
        "opd_063",
        "assemble",
        "materialize",
        "canonical",
        "condition",
        "learned",
        "freeze_predictions",
        "prediction_ledger",
    )):
        print(f"{i}: {line}")

print("[RESULT] EXACT UPSTREAM AND LEDGER BOUNDARIES EXPOSED")