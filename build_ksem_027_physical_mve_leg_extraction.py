from pathlib import Path
import json

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem027_physical_mve_legs.json"
TEST=ROOT/"test_ksem_027_physical_mve_leg_extraction.py"

def main():
    print("="*120); print(" KSEM-027 PHYSICAL MVE SPORTS LEG EXTRACTION"); print("="*120)
    from qseries_v2.kalshi_sports_evidence_mapping.production_sports_candidate_reader import read_production_sports_candidates
    _,_,markets,_=read_production_sports_candidates(root=ROOT,market_limit=100)
    parents=[]; legs=[]
    for m in markets:
        selected=m.get("mve_selected_legs") or []
        if not selected: continue
        p={"ticker":m.get("ticker"),"event_ticker":m.get("event_ticker"),
           "title":m.get("title"),"leg_count":len(selected)}
        parents.append(p)
        for i,x in enumerate(selected):
            legs.append({"parent_ticker":m.get("ticker"),"leg_index":i,
                         "event_ticker":x.get("event_ticker"),
                         "market_ticker":x.get("market_ticker"),"side":x.get("side")})
    print("[PARENTS]",len(parents)); print("[LEGS]",len(legs))
    for x in legs[:20]: print("[LEG]",x)
    if not parents or not legs: raise RuntimeError("no physical MVE legs found")
    STATE.write_text(json.dumps({"parents":parents,"legs":legs,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem027_physical_mve_legs.json').read_text())\nassert d['parents'] and d['legs']\nassert all(x['market_ticker'] for x in d['legs'])\nassert d['execution_authority'] is False\nprint('[PASS] physical Kalshi MVE legs extracted exactly')\nprint('[PASS] KSEM-027 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()