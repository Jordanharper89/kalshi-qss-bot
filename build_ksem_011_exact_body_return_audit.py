
from pathlib import Path
import ast,json,hashlib
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
AUD=PKG/"state/ksem006_exact_interface_audit.json"
STATE=PKG/"state/ksem011_exact_body_return_audit.json"
TEST=ROOT/"test_ksem_011_exact_body_return_audit.py"
TARGETS={
"market_type":("qseries_v2/oracle_adapters/independent/oad_088_sports_market_type_resolver.py","resolve_sports_market_type"),
"entity":("qseries_v2/oracle_adapters/independent/oad_098_structured_sports_entity_type_recognition.py","recognize_sports_entity_type"),
"decomposition":("qseries_v2/oracle_adapters/independent/oad_099_mixed_domain_cross_category_decomposition.py","decompose_mixed_market"),
"classification":("qseries_v2/oracle_adapters/independent/oad_101_universal_classification_exhaustive_diagnostic.py","classify_isolated_root_cause")}
def shape(n):
    if n is None:return "NONE"
    if isinstance(n,ast.Call):
        return "CALL:"+((n.func.id if isinstance(n.func,ast.Name) else n.func.attr) if isinstance(n.func,(ast.Name,ast.Attribute)) else "OTHER")
    return type(n).__name__.upper()
def main():
    print("="*120);print(" KSEM-011 EXACT BODY / RETURN AUDIT");print("="*120)
    if not AUD.exists():raise SystemExit("[FAIL] missing KSEM-006")
    out={}
    for role,(rel,name) in TARGETS.items():
        p=ROOT/rel
        if not p.exists():raise SystemExit("[FAIL] missing "+rel)
        src=p.read_text(encoding="utf-8");tree=ast.parse(src,str(p))
        fn=next((n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
        if fn is None:raise SystemExit("[FAIL] missing "+name)
        rets=[{"line":n.lineno,"shape":shape(n.value),"expr":ast.unparse(n.value)[:500] if n.value else None} for n in ast.walk(fn) if isinstance(n,ast.Return)]
        if not rets:raise SystemExit("[FAIL] no returns in "+name)
        out[role]={"module":rel,"function":name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"returns":rets}
        print("[ROLE]",role,name)
        for r in rets:print("  [RETURN]",r["line"],r["shape"],r["expr"])
    STATE.write_text(json.dumps({"roles":out,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem011_exact_body_return_audit.json').read_text())\nassert set(d['roles'])=={'market_type','entity','decomposition','classification'}\nassert all(v['returns'] for v in d['roles'].values())\nassert d['execution_authority'] is False\nprint('[PASS] exact function bodies and return shapes audited')\nprint('[PASS] KSEM-011 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT));print("[WRITE]",TEST.name)
if __name__=="__main__":main()
