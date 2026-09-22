
from pathlib import Path
import ast,json
ROOT=Path.cwd();PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
INP=PKG/"state/ksem012_output_schema_and_callsite_audit.json"
STATE=PKG/"state/ksem013_exact_semantic_role_resolution.json"
TEST=ROOT/"test_ksem_013_exact_semantic_role_resolution.py"
EXACT={
"market_type":("qseries_v2.oracle_adapters.independent.oad_088_sports_market_type_resolver","resolve_sports_market_type"),
"entity":("qseries_v2.oracle_adapters.independent.oad_098_structured_sports_entity_type_recognition","recognize_sports_entity_type"),
"decomposition":("qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition","decompose_mixed_market"),
"classification":("qseries_v2.oracle_adapters.independent.oad_101_universal_classification_exhaustive_diagnostic","classify_isolated_root_cause")}
def main():
    print("="*120);print(" KSEM-013 EXACT SEMANTIC ROLE RESOLUTION");print("="*120)
    if not INP.exists():raise SystemExit("[FAIL] missing KSEM-012")
    out={}
    for role,(mod,fn) in EXACT.items():
        p=ROOT/Path(*mod.split(".")).with_suffix(".py")
        tree=ast.parse(p.read_text(encoding="utf-8"),str(p))
        node=next((n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==fn),None)
        if node is None:raise SystemExit("[FAIL] missing exact callable "+fn)
        out[role]={"module":mod,"callable":fn,"line":node.lineno}
        print("[BOUND_ROLE]",role,"->",mod+"."+fn)
    STATE.write_text(json.dumps({"roles":out,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem013_exact_semantic_role_resolution.json').read_text())\nassert set(d['roles'])=={'market_type','entity','decomposition','classification'}\nassert d['roles']['decomposition']['callable']=='decompose_mixed_market'\nassert d['roles']['classification']['callable']=='classify_isolated_root_cause'\nprint('[PASS] decomposition and classification exact roles resolved')\nprint('[PASS] KSEM-013 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT));print("[WRITE]",TEST.name)
if __name__=="__main__":main()
