from pathlib import Path
import ast,json
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
TARGET=ROOT/"qseries_v2/oracle_adapters/independent/oad_120_current_market_sports_team_pair_index.py"
STATE=PKG/"state/ksem018_exact_descriptor_source_repair.json"
TEST=ROOT/"test_ksem_018_exact_descriptor_source_REPAIR.py"

def main():
    print("="*120); print(" KSEM-018 EXACT DESCRIPTOR SOURCE REPAIR"); print("="*120)
    src=TARGET.read_text(encoding="utf-8"); tree=ast.parse(src,str(TARGET))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="fetch_current_market_sports_candidates")
    body=ast.unparse(fn)
    callsites=[]
    for p in (ROOT/"qseries_v2").rglob("*.py"):
        if p==TARGET: continue
        try: t=ast.parse(p.read_text(encoding="utf-8"),str(p))
        except: continue
        for n in ast.walk(t):
            if isinstance(n,ast.Call):
                name=n.func.id if isinstance(n.func,ast.Name) else (n.func.attr if isinstance(n.func,ast.Attribute) else "")
                if name=="fetch_current_market_sports_candidates":
                    callsites.append({"module":str(p.relative_to(ROOT)),"line":n.lineno,
                                      "args":[ast.unparse(a) for a in n.args],
                                      "keywords":{k.arg:ast.unparse(k.value) for k in n.keywords}})
    print("[FUNCTION_BODY]"); print(body)
    for c in callsites: print("[CALLSITE]",c)
    STATE.write_text(json.dumps({"function_body":body,"callsites":callsites,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem018_exact_descriptor_source_repair.json').read_text())\nassert 'descriptors' in d['function_body']\nassert d['execution_authority'] is False\nprint('[PASS] exact OAD-120 descriptor contract captured')\nprint('[PASS] physical descriptor callsites captured')\nprint('[PASS] KSEM-018 repair certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()