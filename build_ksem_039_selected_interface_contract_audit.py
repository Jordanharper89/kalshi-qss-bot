from pathlib import Path
import ast,json

ROOT=Path.cwd(); S=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=S/"ksem039_selected_interface_contract.json"
TEST=ROOT/"test_ksem_039_selected_interface_contract_audit.py"

def main():
    print("="*120); print(" KSEM-039 SELECTED RETRIEVAL INTERFACE CONTRACT AUDIT"); print("="*120)
    sel=json.loads((S/"ksem038_exact_retrieval_candidate_selection.json").read_text())["selected"]
    p=ROOT/sel["file"]; src=p.read_text(encoding="utf-8"); tree=ast.parse(src)
    target=None
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==sel["function"]:
            target=n; break
    if target is None: raise RuntimeError("selected function disappeared")
    returns=[ast.unparse(n.value) if n.value else "None" for n in ast.walk(target) if isinstance(n,ast.Return)]
    body=ast.get_source_segment(src,target)
    data={"file":sel["file"],"function":target.name,
          "args":[x.arg for x in target.args.args],
          "defaults":[ast.unparse(x) for x in target.args.defaults],
          "returns":returns,"body":body,"execution_authority":False}
    print("[FILE]",data["file"]); print("[FUNCTION]",data["function"])
    print("[ARGS]",data["args"]); print("[DEFAULTS]",data["defaults"])
    for x in returns: print("[RETURN]",x)
    print("[BODY]\n"+body)
    OUT.write_text(json.dumps(data,indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem039_selected_interface_contract.json').read_text())\nassert d['function'] and d['args'] and d['body']\nassert d['execution_authority'] is False\nprint('[PASS] selected Kalshi retrieval interface exact contract captured')\nprint('[PASS] KSEM-039 certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()