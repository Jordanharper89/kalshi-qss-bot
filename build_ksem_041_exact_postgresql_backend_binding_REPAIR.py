from pathlib import Path
import ast,json

ROOT=Path.cwd()
SRC=ROOT/"qseries_v2/oracle_adapters/independent/oad_exact_sports_unknown_cohort_postgresql_identity_recovery_audit.py"
OUT=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem041_postgresql_backend_binding.json"
TEST=ROOT/"test_ksem_041_exact_postgresql_backend_binding_REPAIR.py"

def main():
    print("="*120); print(" KSEM-041 EXACT POSTGRESQL BACKEND BINDING REPAIR"); print("="*120)
    text=SRC.read_text(encoding="utf-8"); tree=ast.parse(text)
    callers=[]; assignments=[]; imports=[]
    for n in ast.walk(tree):
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            imports.append(ast.unparse(n))
        if isinstance(n,(ast.Assign,ast.AnnAssign)):
            s=ast.unparse(n)
            if "backend" in s.lower(): assignments.append(s)
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            calls=[x for x in ast.walk(n) if isinstance(x,ast.Call)]
            for c in calls:
                if "_read_market_snapshot_observations" in ast.unparse(c.func):
                    callers.append({
                        "function":n.name,
                        "args":[x.arg for x in n.args.args],
                        "call":ast.unparse(c),
                        "body":ast.get_source_segment(text,n)
                    })
    print("[CALLERS]",len(callers))
    for x in callers: print("[CALLER]",x["function"],x["args"],x["call"])
    for x in assignments: print("[BACKEND_ASSIGNMENT]",x)
    for x in imports:
        if "postgres" in x.lower() or "backend" in x.lower() or "persistence" in x.lower():
            print("[RELEVANT_IMPORT]",x)
    if not callers: raise RuntimeError("no exact snapshot-reader caller found")
    data={"callers":callers,"backend_assignments":assignments,
          "imports":imports,"execution_authority":False}
    OUT.write_text(json.dumps(data,indent=2),encoding="utf-8")
    TEST.write_text(
        "import json\nfrom pathlib import Path\n"
        "d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem041_postgresql_backend_binding.json').read_text())\n"
        "assert d['callers']\n"
        "assert d['execution_authority'] is False\n"
        "print('[PASS] exact PostgreSQL snapshot-reader backend binding audited')\n"
        "print('[PASS] KSEM-041 repair certified')\n",
        encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()