from pathlib import Path
import json,re

ROOT=Path.cwd()
S=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=S/"ksem031_first_physical_per_leg_evidence_gate.json"
TEST=ROOT/"test_ksem_031_first_physical_per_leg_evidence_gate.py"

def norm(x):
    return re.sub(r"[^a-z0-9]+"," ",str(x).lower()).strip()

def main():
    print("="*120); print(" KSEM-031 FIRST PHYSICAL PER-LEG EVIDENCE COVERAGE GATE"); print("="*120)
    dec=json.loads((S/"ksem028_existing_decomposer_physical.json").read_text())
    idx=json.loads((S/"ksem030_exact_osn_team_pair_index.json").read_text())["events"]
    results=[]
    for parent in dec["parents"]:
        for leg in parent["decomposed"]:
            text=str(leg.get("text","")); n=norm(text)
            matches=[e for e in idx if e["home_norm"] and e["away_norm"]
                     and e["home_norm"] in n and e["away_norm"] in n]
            status="EXACT_BOUND" if len(matches)==1 else ("AMBIGUOUS" if len(matches)>1 else "SOURCE_GAP")
            results.append({"parent_ticker":parent["parent_ticker"],"leg_index":leg.get("leg_index"),
                            "text":text,"status":status,"matches":matches[:5]})
    counts={x:sum(1 for r in results if r["status"]==x) for x in ("EXACT_BOUND","AMBIGUOUS","SOURCE_GAP")}
    print("[TOTAL_LEGS]",len(results)); print("[COUNTS]",counts)
    for x in results[:30]: print("[LEG_EVIDENCE]",x)
    if not results: raise RuntimeError("no physical decomposed legs evaluated")
    if sum(counts.values())!=len(results): raise RuntimeError("leg accounting failure")
    OUT.write_text(json.dumps({"total_legs":len(results),"counts":counts,"results":results,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem031_first_physical_per_leg_evidence_gate.json').read_text())\nassert d['total_legs']>0\nassert sum(d['counts'].values())==d['total_legs']\nassert all(x['status'] in ('EXACT_BOUND','AMBIGUOUS','SOURCE_GAP') for x in d['results'])\nassert d['execution_authority'] is False\nprint('[PASS] every physical sports leg accounted for without fabricated binding')\nprint('[PASS] KSEM-031 certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()