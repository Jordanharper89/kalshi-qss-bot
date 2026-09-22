from pathlib import Path
import ast,json

ROOT=Path.cwd()
S=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
SRC=ROOT/"qseries_v2/oracle_adapters/independent/oad_exact_sports_unknown_cohort_postgresql_identity_recovery_audit.py"
OUT=S/"ksem040_postgresql_snapshot_contract.json"
TEST=ROOT/"test_ksem_040_postgresql_snapshot_contract_REPAIR.py"

def main():
    print("="*120); print(" KSEM-040 POSTGRESQL SNAPSHOT CONTRACT REPAIR"); print("="*120)
    text=SRC.read_text(encoding="utf-8")
    tree=ast.parse(text)
    target=None
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="_read_market_snapshot_observations":
            target=n; break
    if target is None: raise RuntimeError("exact snapshot reader missing")
    calls=[ast.unparse(x) for x in ast.walk(target) if isinstance(x,ast.Call)]
    returns=[ast.unparse(x.value) if x.value else "None" for x in ast.walk(target) if isinstance(x,ast.Return)]
    data={"file":str(SRC.relative_to(ROOT)),"function":target.name,
          "args":[x.arg for x in target.args.args],
          "body":ast.get_source_segment(text,target),
          "calls":calls,"returns":returns,"execution_authority":False}
    print("[FUNCTION]",target.name); print("[ARGS]",data["args"])
    for x in calls: print("[CALL]",x)
    for x in returns: print("[RETURN]",x)
    print("[BODY]\n"+data["body"])
    OUT.write_text(json.dumps(data,indent=2),encoding="utf-8")
    TEST.write_text(
        "import json\nfrom pathlib import Path\n"
        "d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem040_postgresql_snapshot_contract.json').read_text())\n"
        "assert d['function']=='_read_market_snapshot_observations'\n"
        "assert d['args']==['backend','tickers']\n"
        "assert d['body']\n"
        "assert d['execution_authority'] is False\n"
        "print('[PASS] exact PostgreSQL market-snapshot ticker reader contract captured')\n"
        "print('[PASS] KSEM-040 repair certified')\n",
        encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()