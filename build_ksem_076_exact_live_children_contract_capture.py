from pathlib import Path
import ast, hashlib, json
ROOT=Path.cwd(); STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
TEST=ROOT/"test_ksem_076_exact_live_children_contract_capture.py"
def main():
    print("="*120); print(" KSEM-076 EXACT LIVE CHILDREN CONTRACT CAPTURE INSTALLER"); print("="*120)
    launcher=ROOT/"run_oracle_LIVE.py"
    if not launcher.is_file(): raise RuntimeError("run_oracle_LIVE.py missing")
    src=launcher.read_text(encoding="utf-8")
    tree=ast.parse(src)
    children=None
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in node.targets):
            children=ast.literal_eval(node.value); break
    if not isinstance(children,dict): raise RuntimeError("CHILDREN is not a literal dict")
    report={"schema_version":"KSEM-076","launcher_sha256":hashlib.sha256(src.encode()).hexdigest(),
            "launcher_lines":len(src.splitlines()),"children":children,
            "has_start_function":any(isinstance(n,ast.FunctionDef) and n.name=="_start" for n in tree.body),
            "has_run_forever":any(isinstance(n,ast.FunctionDef) and n.name=="run_forever" for n in tree.body)}
    STATE.mkdir(parents=True,exist_ok=True)
    (STATE/"ksem076_live_children_contract.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    TEST.write_text("""from pathlib import Path\nimport json\nr=json.loads((Path.cwd()/'qseries_v2/kalshi_sports_evidence_mapping/state/ksem076_live_children_contract.json').read_text())\nprint('[CONTRACT]',r)\nassert isinstance(r['children'],dict) and 'sports' in r['children']\nassert 'ksem_mapping' not in r['children']\nassert r['has_start_function'] and r['has_run_forever']\nprint('[PASS] exact production CHILDREN dict captured before cutover')\nprint('[PASS] KSEM-076 certified')\n""",encoding="utf-8")
    print("[CONTRACT]",report)
    print("[PASS] run_oracle_LIVE.py captured read-only")
    print("[PASS] KSEM-076 installer complete")
if __name__=="__main__": main()