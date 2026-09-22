from pathlib import Path
import ast, re

ROOT=Path.cwd().resolve()
PRED=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
CHILD=ROOT/"run_opd_full_evidence_predictor_child.py"

if not PRED.exists():
    raise SystemExit("[FAIL] predictor missing: "+str(PRED))

src=PRED.read_text(encoding="utf-8")
tree=ast.parse(src)

funcs=[n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
print("="*110)
print(" OPD FULL-EVIDENCE ACTUAL ENTRYPOINT DIAGNOSTIC")
print("="*110)
print("[PREDICTOR]",PRED)
print("[TOP-LEVEL FUNCTIONS]",len(funcs))
for f in funcs:
    print("[FUNCTION]",f)

if CHILD.exists():
    cs=CHILD.read_text(encoding="utf-8")
    print("[CHILD]",CHILD)

    imports=re.findall(
        r"from\s+qseries_v2\.oracle_predictive_discovery\.opd_live_full_evidence_fusion_predictor\s+import\s+([^\n]+)",
        cs
    )
    for x in imports:
        print("[CHILD IMPORT]",x.strip())

    for f in funcs:
        if re.search(r"\b"+re.escape(f)+r"\s*\(",cs):
            print("[CHILD CALL]",f)

    print("[CHILD RELEVANT LINES]")
    for line in cs.splitlines():
        low=line.lower()
        if "fusion_predictor" in low or any(re.search(r"\b"+re.escape(f)+r"\s*\(",line) for f in funcs):
            print(line)
else:
    print("[WARN] run_opd_full_evidence_predictor_child.py not found at repo root")

print("[RESULT] USE CHILD CALL AS PHYSICAL PRODUCTION ENTRYPOINT")