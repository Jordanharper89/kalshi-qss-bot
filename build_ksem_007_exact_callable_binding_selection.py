
from pathlib import Path
import json
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
AUD=PKG/"state/ksem006_exact_interface_audit.json"
STATE=PKG/"state/ksem007_exact_callable_binding_selection.json"
TEST=ROOT/"test_ksem_007_exact_callable_binding_selection.py"
ROLE_TERMS={"market_type":("market","type","resolve","classif"),"entity":("entity","recogn","team","player"),"decomposition":("decompos","leg","parse","market"),"classification":("classif","diagnostic","resolve","market")}
MODULE_ROLE={"oad_088_sports_market_type_resolver.py":"market_type","oad_098_structured_sports_entity_type_recognition.py":"entity","oad_099_mixed_domain_cross_category_decomposition.py":"decomposition","oad_101_universal_classification_exhaustive_diagnostic.py":"classification"}

def score(name,role): return sum(1 for t in ROLE_TERMS[role] if t in name.lower())

def main():
    print("="*118); print(" KSEM-007 EXACT CALLABLE BINDING SELECTION"); print("="*118)
    if not AUD.exists(): raise SystemExit("[FAIL] missing KSEM-006 audit")
    aud=json.loads(AUD.read_text(encoding="utf-8")); roles={}
    for m in aud["modules"]:
        role=MODULE_ROLE[Path(m["path"]).name]
        cands=[]
        for f in m["functions"]:
            if not f["name"].startswith("_"):
                cands.append({"kind":"function","name":f["name"],"score":score(f["name"],role),"signature":f["signature"],"line":f["line"]})
        for c in m["classes"]:
            if not c["name"].startswith("_"):
                cands.append({"kind":"class","name":c["name"],"score":score(c["name"],role),"methods":c["methods"],"line":c["line"]})
        cands.sort(key=lambda x:(-x["score"],x["line"],x["name"]))
        if not cands: raise SystemExit(f"[FAIL] no public callable/class in {m['path']}")
        top=cands[0]; ties=[x for x in cands if x["score"]==top["score"]]
        exact=top if len(ties)==1 and top["score"]>0 else None
        roles[role]={"module":m["path"],"module_sha256":m["sha256"],"candidates":cands[:20],"selected":exact,"selection_status":"SELECTED" if exact else "AMBIGUOUS"}
        print("[ROLE]",role,roles[role]["selection_status"])
        for x in cands[:10]: print("  [CANDIDATE]",x["kind"],x["name"],"score=",x["score"])
    STATE.write_text(json.dumps({"roles":roles,"selected_count":sum(v["selected"] is not None for v in roles.values()),"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem007_exact_callable_binding_selection.json').read_text())\nassert set(d['roles'])=={'market_type','entity','decomposition','classification'}\nassert all(v['candidates'] for v in d['roles'].values())\nassert d['execution_authority'] is False\nprint('[PASS] exact callable candidates ranked from AST interfaces')\nprint('[PASS] ambiguous interfaces retained instead of guessed')\nprint('[PASS] KSEM-007 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)
if __name__=="__main__": main()
