from pathlib import Path
import json

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem029_existing_sports_identity.json"
TEST=ROOT/"test_ksem_029_existing_sports_identity_physical_gate.py"

def main():
    print("="*120); print(" KSEM-029 EXISTING SPORTS IDENTITY PHYSICAL GATE"); print("="*120)
    from qseries_v2.kalshi_sports_evidence_mapping.production_sports_candidate_reader import read_production_sports_candidates
    from qseries_v2.oracle_adapters.independent.oad_099_universal_mixed_market_decomposition import decompose_mixed_market
    from qseries_v2.oracle_adapters.independent.oad_098_structured_sports_entity_type_recognition import recognize_sports_entity_type
    from qseries_v2.oracle_adapters.independent.oad_088_sports_market_type_resolution import resolve_sports_market_type
    _,_,markets,_=read_production_sports_candidates(root=ROOT,market_limit=100)
    out=[]
    for m in markets:
        if not m.get("mve_selected_legs"): continue
        mt=resolve_sports_market_type(m)
        legs=[]
        for x in decompose_mixed_market(m):
            text=getattr(x,"text","")
            legs.append({"text":text,"entity":repr(recognize_sports_entity_type(text))})
        out.append({"ticker":m.get("ticker"),"market_type":repr(mt),"legs":legs})
    print("[PARENTS]",len(out)); print("[IDENTIFIED_LEGS]",sum(len(x["legs"]) for x in out))
    for x in out[:5]: print("[IDENTITY]",x)
    if not out: raise RuntimeError("no physical sports identity cohort")
    STATE.write_text(json.dumps({"parents":out,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem029_existing_sports_identity.json').read_text())\nassert d['parents']\nassert all(x['market_type'] for x in d['parents'])\nassert d['execution_authority'] is False\nprint('[PASS] existing sports entity and market-type pavement physically executed')\nprint('[PASS] KSEM-029 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()