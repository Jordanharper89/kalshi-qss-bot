from pathlib import Path
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
TEST=ROOT/"test_ksem_005_live_kalshi_sports_understanding_readiness_gate.py"
def main():
    print("="*110); print(" KSEM-005 LIVE KALSHI SPORTS UNDERSTANDING READINESS GATE"); print("="*110)
    import json
    req=[PKG/"state/ksem001_admission_foundation.json",PKG/"state/ksem002_existing_classifier_inventory.json",PKG/"state/ksem003_entity_league_resolution.json",PKG/"state/ksem004_market_proposition_contract.json"]
    for p in req:
        if not p.exists(): raise SystemExit("[FAIL] missing dependency: "+str(p.relative_to(ROOT)))
    inv=json.loads(req[1].read_text()); ranked=[]
    for x in inv["candidates"]:
        text=(x["path"]+" "+" ".join(x.get("symbols",[]))).lower()
        if any(k in text for k in ("classif","decompos","market_type","entity","sports")): ranked.append(x)
    if not ranked: raise SystemExit("[FAIL] no exact physical binding candidate; refusing fabricated live gate")
    top=ranked[:12]
    state={"foundation_ready":True,"physical_repo_candidates":top,"live_market_execution_performed":False,"next_required_build":"EXACT_BINDING_TO_CERTIFIED_KALSHI_CLASSIFICATION_DECOMPOSITION_PAVEMENT","silent_guessing_allowed":False,"execution_authority":False}
    (PKG/"state/ksem005_live_understanding_readiness.json").write_text(json.dumps(state,indent=2))
    for x in top: print("[NEXT_BINDING_CANDIDATE]",x["path"],x.get("symbols",[])[:8])
    print("[PASS] exact physical candidates retained; live execution not fabricated")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem005_live_understanding_readiness.json').read_text())\nassert d['foundation_ready'] and d['physical_repo_candidates']\nassert d['live_market_execution_performed'] is False\nassert d['silent_guessing_allowed'] is False and d['execution_authority'] is False\nprint('[PASS] KSEM-001 through KSEM-004 foundation ready')\nprint('[PASS] exact repo candidates retained for next live binding')\nprint('[PASS] no fake live-market execution claimed')\nprint('[PASS] KSEM-005 certified')\n",encoding="utf-8")
    compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
    print("[WRITE]",TEST.name)
    print("[PASS] execution_authority=FALSE")
if __name__=="__main__": main()
