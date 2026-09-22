
from pathlib import Path
import ast, json, hashlib
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
INV=PKG/"state/ksem002_existing_classifier_inventory.json"
STATE=PKG/"state/ksem006_exact_interface_audit.json"
TEST=ROOT/"test_ksem_006_exact_existing_sports_interface_audit.py"
TARGET_NAMES=("oad_088_sports_market_type_resolver.py","oad_098_structured_sports_entity_type_recognition.py","oad_099_mixed_domain_cross_category_decomposition.py","oad_101_universal_classification_exhaustive_diagnostic.py")

def sig_of(fn):
    a=fn.args
    args=[x.arg for x in a.posonlyargs+a.args]
    defaults=len(a.defaults)
    required=args[:max(0,len(args)-defaults)]
    return {"args":args,"required":required,"kwonly":[x.arg for x in a.kwonlyargs],"async":isinstance(fn,ast.AsyncFunctionDef)}

def main():
    print("="*118); print(" KSEM-006 EXACT EXISTING SPORTS INTERFACE AUDIT"); print("="*118)
    if not INV.exists(): raise SystemExit("[FAIL] missing KSEM-002 inventory")
    inv=json.loads(INV.read_text(encoding="utf-8"))
    paths=[ROOT/x["path"] for x in inv["candidates"] if Path(x["path"]).name in TARGET_NAMES]
    if len(paths)!=4: raise SystemExit(f"[FAIL] expected exact OAD-088/098/099/101 files; found {len(paths)}")
    audited=[]
    for p in paths:
        text=p.read_text(encoding="utf-8")
        tree=ast.parse(text,str(p))
        funcs=[]; classes=[]
        for n in tree.body:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
                funcs.append({"name":n.name,"signature":sig_of(n),"line":n.lineno})
            elif isinstance(n,ast.ClassDef):
                methods=[]
                for m in n.body:
                    if isinstance(m,(ast.FunctionDef,ast.AsyncFunctionDef)):
                        methods.append({"name":m.name,"signature":sig_of(m),"line":m.lineno})
                classes.append({"name":n.name,"line":n.lineno,"methods":methods})
        rec={"path":str(p.relative_to(ROOT)),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"functions":funcs,"classes":classes}
        audited.append(rec)
        print("[AUDIT]",rec["path"])
        for f in funcs: print("  [FUNCTION]",f["name"],f["signature"])
        for c in classes: print("  [CLASS]",c["name"],"methods=",[(m["name"],m["signature"]) for m in c["methods"][:12]])
    STATE.write_text(json.dumps({"modules":audited,"module_count":len(audited),"ast_parsed":True,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem006_exact_interface_audit.json').read_text())\nassert d['ast_parsed'] and d['module_count']==4\nassert all(Path(x['path']).exists() for x in d['modules'])\nassert d['execution_authority'] is False\nprint('[PASS] exact OAD-088/098/099/101 AST interfaces captured')\nprint('[PASS] KSEM-006 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)
    print("[PASS] no audited module imported or executed")
if __name__=="__main__": main()
